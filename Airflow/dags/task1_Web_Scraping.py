import requests
from bs4 import BeautifulSoup
import logging
import os
import io
import subprocess
from google.cloud import storage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve the environment variables
hugging_face_token = os.getenv("HUGGING_FACE_TOKEN")
gcp_key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
base_url = os.getenv("BASE_URL")
test_directory_url = os.getenv("TEST_DIRECTORY_URL")
validation_directory_url = os.getenv("VALIDATION_DIRECTORY_URL")

# GCP Bucket name
gcp_bucket_name = "gaia_files_pdfs_sample"

def fetch_pdf_file_names(directory_url):
    try:
        print(f"Fetching PDF file names from {directory_url}")
        response = requests.get(directory_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        pdf_files = [a['href'].split('/')[-1] for a in soup.find_all('a') if a['href'].endswith('.pdf')]
        logging.info(f"Found {len(pdf_files)} PDF files in {directory_url}")
        print(f"Found {len(pdf_files)} PDF files in {directory_url}")
        return pdf_files
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching PDFs from {directory_url}: {http_err}")
        print(f"HTTP error occurred: {http_err}")
        raise
    except Exception as err:
        logging.error(f"Error occurred while fetching PDFs from {directory_url}: {err}")
        print(f"Error occurred: {err}")
        raise

def download_file(file_name, download_folder):
    try:
        print(f"Downloading file {file_name} from {download_folder}")
        file_url = f"{base_url}{download_folder}/{file_name}"
        headers = {"Authorization": f"Bearer {hugging_face_token}"}
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        logging.info(f"Successfully downloaded {file_name} from {download_folder}")
        print(f"Successfully downloaded {file_name}")
        return response.content  # Return the content as bytes
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while downloading {file_name}: {http_err}")
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Error occurred while downloading {file_name}: {err}")
        print(f"Error occurred: {err}")
    return None

def compress_pdf_with_ghostscript(pdf_bytes, max_size=4 * 1024 * 1024):
    """Compress PDF using Ghostscript."""
    try:
        input_io = io.BytesIO(pdf_bytes)
        
        print("Compressing PDF with Ghostscript")
        
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
            print(f"Compressed size: {compressed_size / (1024 * 1024):.2f} MB with quality setting {quality}")
            
            if compressed_size <= max_size:
                logging.info("Compression successful.")
                print("Compression successful")
                return compressed_pdf_bytes
            
        logging.warning("Could not compress below the target size with Ghostscript.")
        print("Could not compress below target size")
        return compressed_pdf_bytes  # Return the best we could get
        
    except Exception as e:
        logging.error(f"Error during PDF compression with Ghostscript: {e}")
        print(f"Error during PDF compression: {e}")
        raise
    finally:
        # Clean up temporary files
        if os.path.exists('input.pdf'):
            os.remove('input.pdf')
        if os.path.exists('output.pdf'):
            os.remove('output.pdf')

def upload_to_gcp_bucket(file_name, file_content, folder_name):
    try:
        print(f"Uploading {file_name} to GCP bucket")
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcp_bucket_name)
        blob = bucket.blob(f"{folder_name}/{file_name}")
        blob.upload_from_string(file_content, content_type='application/pdf')
        logging.info(f"Uploaded {file_name} to bucket {gcp_bucket_name}/{folder_name}")
        print(f"Uploaded {file_name} to GCP bucket")
    except Exception as e:
        logging.error(f"Failed to upload {file_name} to GCS: {e}")
        print(f"Failed to upload {file_name}: {e}")
        raise

def process_files(download_folder, directory_url):
    print(f"Processing files from {directory_url}")
    file_list = fetch_pdf_file_names(directory_url)
    if not file_list:
        logging.warning(f"No files fetched for folder: {download_folder}")
        print(f"No files fetched for folder: {download_folder}")
        return
    for file_name in file_list:
        logging.info(f"Processing file: {file_name} from Hugging Face folder: {download_folder}")
        print(f"Processing file: {file_name}")
        content = download_file(file_name, download_folder)
        if content:
            original_size = len(content)
            logging.info(f"Original size of {file_name}: {original_size / (1024 * 1024):.2f} MB")
            print(f"Original size of {file_name}: {original_size / (1024 * 1024):.2f} MB")
            if original_size > 4 * 1024 * 1024:
                logging.info(f"{file_name} is larger than 4MB. Compressing...")
                print(f"{file_name} is larger than 4MB. Compressing...")
                try:
                    content = compress_pdf_with_ghostscript(content)
                    compressed_size = len(content)
                    logging.info(f"Compressed size of {file_name}: {compressed_size / (1024 * 1024):.2f} MB")
                    print(f"Compressed size of {file_name}: {compressed_size / (1024 * 1024):.2f} MB")
                except Exception as e:
                    logging.error(f"Compression failed for {file_name}: {e}")
                    print(f"Compression failed for {file_name}: {e}")
                    continue  # Skip uploading if compression fails
            else:
                logging.info(f"{file_name} is less than 4MB. No compression needed.")
                print(f"{file_name} is less than 4MB. No compression needed.")
            # Upload to 'gaia_pdfs' folder
            upload_to_gcp_bucket(file_name, content, 'gaia_pdfs')
        else:
            logging.warning(f"Skipping upload for {file_name} due to download failure.")
            print(f"Skipping upload for {file_name} due to download failure.")

#def main():
    # Existing code under if __name__ == "__main__":
    # Process files from the test directory
#    print("Starting PDF processing for test directory...")
#    process_files("test", test_directory_url)

    # Process files from the validation directory
 #   print("Starting PDF processing for validation directory...")
 #   process_files("validation", validation_directory_url)

if __name__ == "__main__":
    # Process files from the test directory
    print("Starting PDF processing for test directory...")
    process_files("test", test_directory_url)

    # Process files from the validation directory
    print("Starting PDF processing for validation directory...")
    process_files("validation", validation_directory_url)
