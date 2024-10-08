# extract_text_opensource.py

import os
import logging
import io
from google.cloud import storage
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# GCP Bucket name
gcp_bucket_name = "gaia_files_pdf"

# Tesseract command path
tesseract_cmd_path = "/usr/bin/tesseract"  # Adjust this path if necessary
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

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

def extract_text_opensource(target_folder):
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
