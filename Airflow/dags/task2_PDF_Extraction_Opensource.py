import os
import io
import pdfplumber
from google.cloud import storage
import pytesseract
from PIL import Image
import fitz  # PyMuPDF for more efficient image extraction
from dotenv import load_dotenv
import cv2
import numpy as np

# Load environment variables from the .env file
load_dotenv()

# Set the GCP credentials and Tesseract path from .env
gcp_key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
tesseract_cmd_path = os.getenv("TESSERACT_CMD_PATH")
bucket_name = os.getenv("GCP_BUCKET_NAME")
source_folder = os.getenv("SOURCE_FOLDER")
target_folder = os.getenv("TARGET_FOLDER")

# Set the path to the GCP credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_key_file

# Initialize GCP storage client
storage_client = storage.Client()

# Initialize Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

def preprocess_image(image):
    """Preprocess image to improve OCR results."""
    img = np.array(image)

    # Check the number of channels
    if len(img.shape) == 2:
        # Single-channel grayscale image, no need to convert
        gray = img
    elif len(img.shape) == 3:
        if img.shape[2] == 3:
            # 3-channel RGB image, convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif img.shape[2] == 4:
            # 4-channel RGBA image, convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        else:
            print(f"Unsupported number of channels: {img.shape[2]}")
            return None
    else:
        print(f"Unexpected image shape: {img.shape}")
        return None

    # Apply adaptive thresholding to improve text extraction
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    return thresh

def format_table(table):
    """Formats the extracted table rows into structured, aligned output."""
    formatted_table = ""
    max_lengths = [max(len(str(cell)) if cell else 0 for cell in col) for col in zip(*table)]

    for row in table:
        formatted_row = " | ".join([str(cell).ljust(max_len) if cell else ''.ljust(max_len) for cell, max_len in zip(row, max_lengths)])
        formatted_table += formatted_row + "\n"
    return formatted_table

def extract_text_and_tables(pdf_data):
    """Extracts text and tables from the PDF using pdfplumber."""
    extracted_text = ""
    structured_data = []

    # Process the PDF data using pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Extract tables first to avoid duplicate extraction in plain text
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    formatted_table = format_table(table)
                    structured_data.append({
                        "page_number": page_num,
                        "tables": formatted_table
                    })
            else:
                # Extract text from the page if no tables
                extracted_text += f"Page {page_num} Text:\n"
                extracted_text += page.extract_text() or ""

    return extracted_text, structured_data

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

                # Preprocess the image
                preprocessed_img = preprocess_image(img)

                # Only proceed if preprocessing is successful
                if preprocessed_img is not None:
                    # Apply OCR to extract text from the preprocessed image
                    extracted_image_text = pytesseract.image_to_string(preprocessed_img, config="--psm 6")

                    image_text += f"\n\nPage {page_num + 1}, Image {img_index + 1} OCR Text:\n{extracted_image_text}"
                else:
                    print(f"Skipping image on page {page_num + 1}, image {img_index + 1} due to processing error")

            except Exception as e:
                print(f"Error processing image on page {page_num + 1}, image {img_index + 1}: {e}")
   
    return image_text

def extract_pdf_data_from_gcp(bucket_name, folder_name, file_name):
    """Extracts text, tables, and images (with OCR) from a PDF stored in GCP."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"{folder_name}/{file_name}")
   
    # Read the file as bytes
    pdf_data = blob.download_as_bytes()

    # Step 1: Extract text and tables
    extracted_text, structured_data = extract_text_and_tables(pdf_data)

    # Step 2: Extract images and apply OCR
    image_text = extract_images_and_apply_ocr(pdf_data)

    # Combine extracted text, tables, and image text
    full_extracted_content = extracted_text

    # Add structured table data to the extracted content
    for table_data in structured_data:
        full_extracted_content += f"\n\nPage {table_data['page_number']} Tables:\n"
        full_extracted_content += table_data['tables']

    # Add image-extracted text
    full_extracted_content += f"\n\nExtracted Text from Images:\n{image_text}"

    return full_extracted_content

def save_extracted_data_to_gcp(bucket_name, folder_name, file_name, extracted_content):
    """Saves the extracted content as a .txt file to the specified GCP bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
   
    # Remove '.pdf' extension and replace with '.txt'
    txt_file_name = file_name.replace('.pdf', '.txt')
   
    # Define the target folder (opensource_extracted)
    blob = bucket.blob(f"{folder_name}/{txt_file_name}")
   
    # Upload the extracted content as a text file
    blob.upload_from_string(extracted_content, content_type='text/plain')
   
    print(f"Extracted data saved to: {folder_name}/{txt_file_name} in bucket {bucket_name}")

# Processing pipeline for all PDFs in the GCP bucket
def process_pdfs_in_gcp(bucket_name, source_folder, target_folder):
    """Processes all PDFs in the source folder of GCP bucket and stores extracted data in the target folder."""
    bucket = storage_client.bucket(bucket_name)
   
    # List all PDF files in the source folder
    blobs = bucket.list_blobs(prefix=f"{source_folder}/")
   
    for blob in blobs:
        if blob.name.endswith('.pdf'):
            file_name = os.path.basename(blob.name)
            print(f"Processing file: {file_name}")
           
            # Extract content from the PDF file
            extracted_content = extract_pdf_data_from_gcp(bucket_name, source_folder, file_name)
           
            # Save extracted content back to GCP in the target folder
            save_extracted_data_to_gcp(bucket_name, target_folder, file_name, extracted_content)

# Example usage:
bucket_name = 'gaia_files_pdf'
source_folder = 'gaia_pdfs'  
target_folder = 'opensource_extracted'

# Run the processing pipeline
process_pdfs_in_gcp(bucket_name, source_folder, target_folder)
