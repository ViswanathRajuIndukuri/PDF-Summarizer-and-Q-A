from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from google.cloud import storage
import requests
from bs4 import BeautifulSoup
import logging
import os
import io
import subprocess
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import tempfile
import cloudmersive_convert_api_client
from cloudmersive_convert_api_client.rest import ApiException as ConvertApiException
import cloudmersive_ocr_api_client
from cloudmersive_ocr_api_client.rest import ApiException as OcrApiException

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Hugging Face base URLs
base_url = "https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/"
test_directory_url = "https://huggingface.co/datasets/gaia-benchmark/GAIA/tree/main/2023/test"
validation_directory_url = "https://huggingface.co/datasets/gaia-benchmark/GAIA/tree/main/2023/validation"

# Hugging Face token
hugging_face_token = os.getenv("HUGGING_FACE_TOKEN")  # Ensure this environment variable is set

# GCP Bucket name
gcp_bucket_name = "gaia_files_pdf"

# Cloudmersive API key
cloudmersive_api_key = os.getenv("CLOUDMERSIVE_API_KEY")  # Ensure this environment variable is set

# Tesseract command path
tesseract_cmd_path = "/usr/bin/tesseract"  # Adjust this path if necessary
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

# Configure Cloudmersive PDF Text Extraction API
convert_configuration = cloudmersive_convert_api_client.Configuration()
convert_configuration.api_key['Apikey'] = cloudmersive_api_key
convert_api_instance = cloudmersive_convert_api_client.ConvertDocumentApi(
    cloudmersive_convert_api_client.ApiClient(convert_configuration)
)

# Configure Cloudmersive OCR API for image extraction
ocr_configuration = cloudmersive_ocr_api_client.Configuration()
ocr_configuration.api_key['Apikey'] = cloudmersive_api_key
ocr_api_instance = cloudmersive_ocr_api_client.ImageOcrApi(
    cloudmersive_ocr_api_client.ApiClient(ocr_configuration)
)

def fetch_pdf_file_names(directory_url, **kwargs):
    try:
        response = requests.get(directory_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        pdf_files = [a['href'].split('/')[-1] for a in soup.find_all('a') if a['href'].endswith('.pdf')]
        logging.info(f"Found {len(pdf_files)} PDF files in {directory_url}")
        return pdf_files
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching PDFs from {directory_url}: {http_err}")
        raise
    except Exception as err:
        logging.error(f"Error occurred while fetching PDFs from {directory_url}: {err}")
        raise

def download_file(file_name, download_folder, **kwargs):
    try:
        file_url = f"{base_url}{download_folder}/{file_name}"
        headers = {"Authorization": f"Bearer {hugging_face_token}"}
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully downloaded {file_name} from {download_folder}")
        return response.content  # Return the content as bytes
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while downloading {file_name}: {http_err}")
    except Exception as err:
        logging.error(f"Error occurred while downloading {file_name}: {err}")
    return None

def compress_pdf_with_ghostscript(pdf_bytes, max_size=4 * 1024 * 1024):
    """Compress PDF using Ghostscript."""
    try:
        input_io = io.BytesIO(pdf_bytes)
        
        # Write the input PDF bytes to a temporary file
        with open('input.pdf', 'wb') as f_in:
            f_in.write(input_io.read())
        
        # Define quality settings to try
        qualities = ['/screen', '/ebook', '/printer', '/prepress']
        
        for quality in qualities:
            gs_command = [
                'gs',
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS={quality}',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                '-sOutputFile=output.pdf',
                'input.pdf'
            ]
            subprocess.run(gs_command, check=True)
            
            with open('output.pdf', 'rb') as f_out:
                compressed_pdf_bytes = f_out.read()
            
            compressed_size = len(compressed_pdf_bytes)
            logging.info(f"Compressed size: {compressed_size / (1024 * 1024):.2f} MB with quality setting {quality}")
            
            if compressed_size <= max_size:
                logging.info("Compression successful.")
                return compressed_pdf_bytes
            
            # If not successful, try the next quality setting
            
        logging.warning("Could not compress below the target size with Ghostscript.")
        return compressed_pdf_bytes  # Return the best we could get
        
    except Exception as e:
        logging.error(f"Error during PDF compression with Ghostscript: {e}")
        raise
    finally:
        # Clean up temporary files
        if os.path.exists('input.pdf'):
            os.remove('input.pdf')
        if os.path.exists('output.pdf'):
            os.remove('output.pdf')

def upload_to_gcp_bucket(file_name, file_content, folder_name, **kwargs):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcp_bucket_name)
        blob = bucket.blob(f"{folder_name}/{file_name}")
        blob.upload_from_string(file_content, content_type='application/pdf')
        logging.info(f"Uploaded {file_name} to bucket {gcp_bucket_name}/{folder_name}")
    except Exception as e:
        logging.error(f"Failed to upload {file_name} to GCS: {e}")
        raise

def process_files(download_folder, **kwargs):
    ti = kwargs['ti']
    file_list = ti.xcom_pull(task_ids=f'fetch_{download_folder}_pdfs')
    if not file_list:
        logging.warning(f"No files fetched for folder: {download_folder}")
        return
    for file_name in file_list:
        logging.info(f"Processing file: {file_name} from Hugging Face folder: {download_folder}")
        content = download_file(file_name, download_folder)
        if content:
            original_size = len(content)
            logging.info(f"Original size of {file_name}: {original_size / (1024 * 1024):.2f} MB")
            # Check if the content size is greater than 4MB
            if original_size > 4 * 1024 * 1024:
                logging.info(f"{file_name} is larger than 4MB. Compressing...")
                try:
                    content = compress_pdf_with_ghostscript(content)
                    compressed_size = len(content)
                    logging.info(f"Compressed size of {file_name}: {compressed_size / (1024 * 1024):.2f} MB")
                except Exception as e:
                    logging.error(f"Compression failed for {file_name}: {e}")
                    continue  # Skip uploading if compression fails
            else:
                logging.info(f"{file_name} is less than 4MB. No compression needed.")
            # Upload to 'gaia_pdfs' folder
            upload_to_gcp_bucket(file_name, content, 'gaia_pdfs')
        else:
            logging.warning(f"Skipping upload for {file_name} due to download failure.")

def extract_text(pdf_data):
    """Extracts text from the PDF using pdfplumber."""
    extracted_text = ""

    # Process the PDF data using pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Add page number heading
            extracted_text += f"\n\nPage {page_num} Text:\n"
            # Extract text from the page
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text

    return extracted_text

def extract_images_and_apply_ocr(pdf_data):
    """Extracts images from PDF using PyMuPDF (fitz) and applies OCR to extract text."""
    image_text = ""
    doc = fitz.open(stream=pdf_data, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Extract all images from the page
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            try:
                # Extract the image bytes
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Open the image using PIL
                img = Image.open(io.BytesIO(image_bytes))

                # Apply OCR to extract text from the image
                extracted_image_text = pytesseract.image_to_string(img)

                image_text += f"\n\nPage {page_num + 1}, Image {img_index + 1}:\n{extracted_image_text}"

            except Exception as e:
                logging.error(f"Error processing image on page {page_num + 1}, image {img_index + 1}: {e}")
    
    return image_text

def save_extracted_data_to_gcp(file_name, extracted_content, target_folder):
    """Saves the extracted content as a .txt file to the specified GCP bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcp_bucket_name)

        # Remove '.pdf' extension and replace with '.txt'
        txt_file_name = file_name.replace('.pdf', '.txt')

        # Define the target folder
        blob = bucket.blob(f"{target_folder}/{txt_file_name}")

        # Upload the extracted content as a text file
        blob.upload_from_string(extracted_content, content_type='text/plain')

        logging.info(f"Extracted data saved to: {target_folder}/{txt_file_name} in bucket {gcp_bucket_name}")
    except Exception as e:
        logging.error(f"Failed to save extracted data for {file_name}: {e}")
        raise

def extract_text_opensource(target_folder, **kwargs):
    """Processes all PDFs in the 'gaia_pdfs/' folder and stores extracted data in the target folder."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcp_bucket_name)

    # List all PDF files in the 'gaia_pdfs/' folder
    blobs = bucket.list_blobs(prefix='gaia_pdfs/')

    for blob in blobs:
        if blob.name.endswith('.pdf'):
            file_name = os.path.basename(blob.name)
            logging.info(f"Processing file: {file_name} with open-source tools")

            # Download the PDF as bytes
            pdf_data = blob.download_as_bytes()

            # Extract content from the PDF file
            extracted_text = extract_text(pdf_data)
            image_text = extract_images_and_apply_ocr(pdf_data)

            # Combine extracted text and image text
            full_extracted_content = extracted_text

            # Always add the 'Extracted Text from Images (OCR):' header
            full_extracted_content += "\n\nExtracted Text from Images (OCR):\n"
            if image_text.strip():
                full_extracted_content += image_text
            else:
                full_extracted_content += "(No text extracted from images.)"

            # Save extracted content back to GCP in the target folder
            save_extracted_data_to_gcp(file_name, full_extracted_content, target_folder)
        else:
            logging.info(f"Skipping non-PDF file: {blob.name}")

def extract_text_from_pdf_cloudmersive(pdf_bytes):
    """Extracts text from PDF using Cloudmersive API."""
    temp_pdf_path = None
    try:
        # Create a temporary file from the PDF bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        # Convert PDF to text using the file path
        result = convert_api_instance.convert_document_pdf_to_txt(temp_pdf_path)  # Pass the path, not the open file

        return result.text_result  # Extract the text result from the object
    except ConvertApiException as e:
        logging.error(f"Exception when calling Cloudmersive API for PDF text extraction: {e}\n")
        return None
    finally:
        # Clean up the temp file if it exists
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

def extract_text_from_images_cloudmersive(pdf_bytes):
    """Extracts text from images embedded in the PDF using Cloudmersive OCR API."""
    temp_pdf_path = None
    try:
        # Create a temporary file from the PDF bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        # Perform OCR on the PDF using the file path
        result = ocr_api_instance.image_ocr_post(temp_pdf_path)  # Adjusted to use ImageOcrApi

        return result.text_result  # This returns the text extracted from images
    except OcrApiException as e:
        logging.error(f"Exception when calling Cloudmersive OCR API: {e}\n")
        return None
    finally:
        # Clean up the temp file if it exists
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

def extract_text_cloudmersive(target_folder, **kwargs):
    """Processes all PDFs in the 'gaia_pdfs/' folder and extracts text using Cloudmersive API."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcp_bucket_name)

    # List all PDF files in the 'gaia_pdfs/' folder
    blobs = bucket.list_blobs(prefix='gaia_pdfs/')

    for blob in blobs:
        if blob.name.endswith('.pdf'):
            file_name = os.path.basename(blob.name)
            logging.info(f"Processing file: {file_name} using Cloudmersive API")

            # Download the PDF as bytes
            pdf_bytes = blob.download_as_bytes()

            # Step 1: Extract text content from the PDF using Cloudmersive API
            extracted_text_content = extract_text_from_pdf_cloudmersive(pdf_bytes)
            # Step 2: Extract text from images using Cloudmersive OCR API
            extracted_image_content = extract_text_from_images_cloudmersive(pdf_bytes)
            # Combine both text and image-extracted content
            extracted_content = ""
            if extracted_text_content:
                extracted_content += extracted_text_content
            if extracted_image_content:
                extracted_content += f"\n\nExtracted Text from Images (OCR):\n{extracted_image_content}"
            if extracted_content:
                # Step 3: Save extracted content back to GCP in the target folder
                save_extracted_data_to_gcp(file_name, extracted_content, target_folder)
        else:
            logging.info(f"Skipping non-PDF file: {blob.name}")

# DAG definition
with DAG(
    'huggingface_to_gcp_with_ghostscript_and_text_extraction',
    default_args=default_args,
    description='Download PDFs from Hugging Face, compress if necessary, extract text, and upload to GCP',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 10, 1),
    catchup=False,
) as dag:

    # Task 1: Fetch Test PDFs
    fetch_test_pdfs = PythonOperator(
        task_id='fetch_test_pdfs',
        python_callable=fetch_pdf_file_names,
        op_kwargs={'directory_url': test_directory_url},
    )

    # Task 2: Fetch Validation PDFs
    fetch_validation_pdfs = PythonOperator(
        task_id='fetch_validation_pdfs',
        python_callable=fetch_pdf_file_names,
        op_kwargs={'directory_url': validation_directory_url},
    )

    # Task 3: Process Test PDFs
    process_test_pdfs = PythonOperator(
        task_id='process_test_pdfs',
        python_callable=process_files,
        op_kwargs={'download_folder': 'test'},
        provide_context=True,
    )

    # Task 4: Process Validation PDFs
    process_validation_pdfs = PythonOperator(
        task_id='process_validation_pdfs',
        python_callable=process_files,
        op_kwargs={'download_folder': 'validation'},
        provide_context=True,
    )

    # Task 5: Extract Text using OpenSource Tools
    extract_text_opensource_task = PythonOperator(
        task_id='extract_text_opensource',
        python_callable=extract_text_opensource,
        op_kwargs={'target_folder': 'opensource_extracted'},
    )

    # Task 6: Extract Text using Cloudmersive API
    extract_text_cloudmersive_task = PythonOperator(
        task_id='extract_text_cloudmersive',
        python_callable=extract_text_cloudmersive,
        op_kwargs={'target_folder': 'cloudmersive_API_extracted'},
    )

    # Define Task Dependencies
    fetch_test_pdfs >> process_test_pdfs
    fetch_validation_pdfs >> process_validation_pdfs
    [process_test_pdfs, process_validation_pdfs] >> extract_text_opensource_task
    [process_test_pdfs, process_validation_pdfs] >> extract_text_cloudmersive_task
