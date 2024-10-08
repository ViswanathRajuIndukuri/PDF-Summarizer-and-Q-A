# dag_gaia_pdf_processing.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import os

# Import the functions from the other files
from fetch_pdfs import process_files as fetch_and_process_pdfs
from extract_text_cloudmersive import extract_text_cloudmersive
from extract_text_opensource import extract_text_opensource

# Hugging Face directory URLs
test_directory_url = "https://huggingface.co/datasets/gaia-benchmark/GAIA/tree/main/2023/test"
validation_directory_url = "https://huggingface.co/datasets/gaia-benchmark/GAIA/tree/main/2023/validation"

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
with DAG(
    'gaia_pdf_processing_dag',
    default_args=default_args,
    description='Process GAIA PDFs: download, compress, extract text, and upload to GCP',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 10, 1),
    catchup=False,
) as dag:

    # Task 1: Process Test PDFs
    process_test_pdfs = PythonOperator(
        task_id='process_test_pdfs',
        python_callable=fetch_and_process_pdfs,
        op_kwargs={
            'download_folder': 'test',
            'directory_url': test_directory_url,
        },
    )

    # Task 2: Process Validation PDFs
    process_validation_pdfs = PythonOperator(
        task_id='process_validation_pdfs',
        python_callable=fetch_and_process_pdfs,
        op_kwargs={
            'download_folder': 'validation',
            'directory_url': validation_directory_url,
        },
    )

    # Task 3: Extract Text using OpenSource Tools
    extract_text_opensource_task = PythonOperator(
        task_id='extract_text_opensource',
        python_callable=extract_text_opensource,
        op_kwargs={'target_folder': 'opensource_extracted'},
    )

    # Task 4: Extract Text using Cloudmersive API
    extract_text_cloudmersive_task = PythonOperator(
        task_id='extract_text_cloudmersive',
        python_callable=extract_text_cloudmersive,
        op_kwargs={'target_folder': 'cloudmersive_API_extracted'},
    )

    # Define Task Dependencies
    [process_test_pdfs, process_validation_pdfs] >> extract_text_opensource_task
    [process_test_pdfs, process_validation_pdfs] >> extract_text_cloudmersive_task
