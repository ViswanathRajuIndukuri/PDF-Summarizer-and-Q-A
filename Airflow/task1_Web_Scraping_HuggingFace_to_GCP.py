import os
import requests
from google.cloud import storage
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the Hugging Face token, Google Cloud credentials, and URLs from .env file
hugging_face_token = os.getenv("HUGGING_FACE_TOKEN")
gcp_key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
base_url = os.getenv("BASE_URL")
test_directory_url = os.getenv("TEST_DIRECTORY_URL")
validation_directory_url = os.getenv("VALIDATION_DIRECTORY_URL")

# Set the path to the Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gcp_key_file

def fetch_pdf_file_names(directory_url):
    """Fetches the names of all PDF files in the specified Hugging Face directory."""
    response = requests.get(directory_url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all links ending with '.pdf'
    pdf_files = [a['href'].split('/')[-1] for a in soup.find_all('a') if a['href'].endswith('.pdf')]
    return pdf_files

def download_file(file_name, folder):
    """Download a single file from the Hugging Face URL."""
    file_url = base_url + f"{folder}/" + file_name  # Choose the correct folder (test or validation)
    headers = {"Authorization": f"Bearer {hugging_face_token}"}
    response = requests.get(file_url, headers=headers)
    
    # Ensure the response is valid
    if response.status_code == 200:
        return response.content  # Return file content for upload
    else:
        print(f"Failed to download {file_name}, HTTP Status: {response.status_code}")
        return None

def upload_to_gcp_bucket(bucket_name, file_name, file_content):
    """Uploads a single file to the GCP bucket under the gaia_pdfs folder."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"gaia_pdfs/{file_name}")  # Save in the gaia_pdfs folder
    blob.upload_from_string(file_content, content_type='application/pdf')
    print(f"Uploaded {file_name} to bucket {bucket_name}/gaia_pdfs")

# Configuration
gcp_bucket_name = "gaia_files_pdf"  # GCP Bucket name

# Step 1: Fetch the PDF file names from the Hugging Face directories
test_pdf_files = fetch_pdf_file_names(test_directory_url)
validation_pdf_files = fetch_pdf_file_names(validation_directory_url)

# Step 2: Download and upload each PDF file from the test folder
for pdf_file in test_pdf_files:
    content = download_file(pdf_file, "test")
    if content:
        upload_to_gcp_bucket(gcp_bucket_name, pdf_file, content)

# Step 3: Download and upload each PDF file from the validation folder
for pdf_file in validation_pdf_files:
    content = download_file(pdf_file, "validation")
    if content:
        upload_to_gcp_bucket(gcp_bucket_name, pdf_file, content)

print("All PDF files from test and validation folders processed into gaia_pdfs folder.")
