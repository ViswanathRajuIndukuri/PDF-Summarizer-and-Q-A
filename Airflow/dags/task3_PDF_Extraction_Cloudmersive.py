import os
import tempfile
import cloudmersive_convert_api_client
from cloudmersive_convert_api_client.rest import ApiException as ConvertApiException
from google.cloud import storage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your Cloudmersive API key and GCP credentials from the .env file
cloudmersive_api_key = os.getenv("CLOUDMERSIVE_API_KEY")
gcp_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Ensure your GCP credentials are set as an environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_credentials

# Initialize GCP storage client
storage_client = storage.Client()

# Configure Cloudmersive PDF Text Extraction API
convert_configuration = cloudmersive_convert_api_client.Configuration()
convert_configuration.api_key['Apikey'] = cloudmersive_api_key
convert_api_instance = cloudmersive_convert_api_client.ConvertDocumentApi(
    cloudmersive_convert_api_client.ApiClient(convert_configuration)
)

def extract_text_from_pdf_cloudmersive(pdf_bytes):
    """Extracts text from PDF using Cloudmersive API."""
    try:
        # Create a temporary file from the PDF bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name
        
        # Convert PDF to text using the file path
        result = convert_api_instance.convert_document_pdf_to_txt(temp_pdf_path)  # Pass the path, not the open file
        
        os.remove(temp_pdf_path)  # Clean up the temporary file
        return result.text_result  # Extract the text result from the object
    except ConvertApiException as e:
        print(f"Exception when calling Cloudmersive API for PDF text extraction: {e}\n")
        return None
    finally:
        # Clean up the temp file if it exists
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

def save_extracted_data_to_gcp(bucket_name, folder_name, file_name, extracted_content):
    """Saves the extracted content as a .txt file to the specified GCP bucket."""
    bucket = storage_client.bucket(bucket_name)
    
    # Remove '.pdf' extension and replace with '.txt'
    txt_file_name = file_name.replace('.pdf', '.txt')
    
    # Define the target folder (e.g., cloudmersive_API_extracted)
    blob = bucket.blob(f"{folder_name}/{txt_file_name}")
    
    # Upload the extracted content as a text file
    blob.upload_from_string(extracted_content, content_type='text/plain')
    
    print(f"Extracted data saved to: {folder_name}/{txt_file_name} in bucket {bucket_name}")

def process_pdfs_in_gcp_cloudmersive(bucket_name, source_folder, target_folder):
    """Processes all PDFs in the source folder, extracts content using Cloudmersive API."""
    bucket = storage_client.bucket(bucket_name)
    
    # List all PDF files in the source folder
    blobs = bucket.list_blobs(prefix=f"{source_folder}/")
    
    for blob in blobs:
        if blob.name.endswith('.pdf'):
            file_name = os.path.basename(blob.name)
            print(f"Processing file: {file_name} using Cloudmersive API")
            
            # Download the PDF as bytes
            pdf_bytes = blob.download_as_bytes()
            
            # Step 1: Extract text content from the PDF using Cloudmersive API
            extracted_text_content = extract_text_from_pdf_cloudmersive(pdf_bytes)
            
            if extracted_text_content:
                # Step 2: Save extracted content back to GCP in the target folder
                save_extracted_data_to_gcp(bucket_name, target_folder, file_name, extracted_text_content)

# Example usage:
bucket_name = 'gaia_files_pdf'
source_folder = 'gaia_pdfs'  # Single folder for PDFs to be processed
target_folder = 'cloudmersive_API_extracted'  # New folder for extracted content

# Process PDFs using Cloudmersive API and save extracted data in cloudmersive_API_extracted folder
process_pdfs_in_gcp_cloudmersive(bucket_name, source_folder, target_folder)
