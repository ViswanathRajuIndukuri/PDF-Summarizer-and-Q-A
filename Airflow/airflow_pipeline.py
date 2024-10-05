from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 10, 4),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1
}

# Define the DAG
with DAG(
    'gaia_text_extraction_pipeline',
    default_args=default_args,
    description='GAIA Text Extraction and Storage Pipeline',
    schedule='@daily',  # Updated to use schedule instead of schedule_interval
    catchup=False
) as dag:

    # Task 1: Call the Python script for web scraping and loading data to GCP
    task_1 = BashOperator(
        task_id='web_scraping_to_gcp',
        bash_command='python task1_Web_Scraping_HuggingFace_to_GCP.py'
    )

    # Task 2: Call the Python script for extracting PDF content using OpenSource (pdfplumber)
    task_2 = BashOperator(
        task_id='extract_pdf_opensource',
        bash_command='python task2_PDF_Extraction_OpenSource.py'
    )

    # Task 3: Call the Python script for extracting PDF content using Cloudmersive API
    task_3 = BashOperator(
        task_id='extract_pdf_cloudmersiveAPI',
        bash_command='python task3_PDF_Extraction_API.py'
    )

    # Task dependencies
    task_1 >> [task_2, task_3]
