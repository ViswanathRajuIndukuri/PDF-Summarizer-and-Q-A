# extract_text_cloudmersive.py

import os
import logging
import tempfile
from google.cloud import storage
import cloudmersive_convert_api_client
from cloudmersive_convert_api_client.rest import ApiException as ConvertApiException
import cloudmersive_ocr_api_client
from cloudmersive_ocr_api_client.rest import ApiException as OcrApiException

# GCP Bucket name
gcp_bucket_name = "gaia_files_pdf"

# Cloudmersive API key
cloudmersive_api_key = os.getenv("CLOUDMERSIVE_API_KEY")  # Ensure this environment variable is set

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

def extract_text_cloudmersive(target_folder):
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
