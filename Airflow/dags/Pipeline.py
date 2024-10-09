import os
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from dotenv import load_dotenv

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['your_email@example.com'],  # Replace with your email
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'gaia_processing_dag',
    default_args=default_args,
    description='A DAG to process Gaia PDFs using BashOperator',
    schedule_interval=None,  # Run on trigger
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

# Use os.environ.get() to retrieve environment variables
env_vars = {
    'HUGGING_FACE_TOKEN': os.environ.get('HUGGING_FACE_TOKEN'),
    'GOOGLE_APPLICATION_CREDENTIALS': os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
    'BASE_URL': os.environ.get('BASE_URL'),
    'TEST_DIRECTORY_URL': os.environ.get('TEST_DIRECTORY_URL'),
    'VALIDATION_DIRECTORY_URL': os.environ.get('VALIDATION_DIRECTORY_URL'),
    'TESSERACT_CMD_PATH': os.environ.get('TESSERACT_CMD_PATH'),
    'CLOUDMERSIVE_API_KEY': os.environ.get('CLOUDMERSIVE_API_KEY'),
}

# Alternatively, if you want to pass all environment variables
# env_vars = os.environ.copy()

scripts_path = '/opt/airflow/dags'  # Since your scripts are in the 'dags' folder

task1 = BashOperator(
    task_id='task1_web_scraping',
    bash_command=f'python {scripts_path}/task1_Web_Scraping.py',
    dag=dag,
    env=env_vars,
)

task2 = BashOperator(
    task_id='task2_pdf_extraction_opensource',
    bash_command=f'python {scripts_path}/task2_PDF_Extraction_Opensource.py',
    dag=dag,
    env=env_vars,
)

task3 = BashOperator(
    task_id='task3_pdf_extraction_cloudmersive',
    bash_command=f'python {scripts_path}/task3_PDF_Extraction_Cloudmersive.py',
    dag=dag,
    env=env_vars,
)

task1 >> task2 >> task3
