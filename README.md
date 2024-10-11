# PDF Summarizer and Q&A
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=apache-airflow&logoColor=white)](https://airflow.apache.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com)



WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR
ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK
Contribution:
- a. Viswanath Raju Indukuri: 33%
- b. Snehal Shivaji Molavade: 33%
- c. Sai Vivekanand Reddy Vangala: 33%

### Individual Contributions
 
This project was completed as a team effort over two weeks, with each member focusing on specific tasks to ensure successful completion. Below are the individual contributions:
 
#### Viswanath Raju Indukuri
- **Streamlit:** Developed and designed the frontend application using streamlit.
- **FastAPI:** Created backend application using FastAPI with multiple API endpoints that are required for application features
- **OpenAI API Integration:** Integrated OpenAI's API into the validation tool for automated responses and evaluation.
 
#### Snehal Shivaji Molavade
- **GCP Cloud Storage and PostgreSQL Setup:** Set up Google Cloud Storage in neccessary format for text extraction.
- **Airflow:** created tasks and designed pipeline for the airflow applicaion to extract text from store it in GCS
- **Text Extraction:** Used different libraries to extract text from the documents in the datasets.
 
#### Sai Vivekanand Reddy Vangala
- **Airflow with Docker:** Improvised the Airflow by running it via docker containers and making sure data acquisition is handled properly
- **Codelab Documentation:** Created comprehensive documentation for the project, detailing steps for setup, deployment, and usage.
- **Architecture Diagram:** Designed the architecture diagram to represent the project's cloud infrastructure and data flow.

## Description
This project focuses on automating the extraction of text from PDF files in the GAIA dataset using Apache Airflow and developing a secure, client-facing application using Streamlit and FastAPI. The objectives are to streamline the process of retrieving and processing documents, ensure that the extracted information is accurately populated into data storage, and provide a user-friendly interface for interaction, including functionalities like summarization and question-answering.

**Documentation**: https://codelabs-preview.appspot.com/?file_id=1QYiFTdbxrUgrE0szRKMQ8sIxHFE_9KpekGauMBp8vzM#0

**Demo Video Link**: https://drive.google.com/drive/folders/1ukDBLyHBy-B8cxhaX4gXOkhiupddNL0J?usp=sharing

**Application URL**: http://viswanath.me:8501/

**Backend Service Link**: http://viswanath.me:8000/docs

## Architecture
![pdf_summarizer_and_q a](https://github.com/user-attachments/assets/069cfbc8-4904-403e-a728-9afcfd6218c8)

## About
**Problem**

The challenge is to create an automated workflow that extracts text from PDFs in the GAIA Benchmarking Validation & Testing Dataset and to develop a secure, user-friendly application that allows users to interact with the extracted data.

**Scope**
+ **Automation**: Automate the data acquisition and text extraction process for PDFs using Airflow.
+ **User Interaction**: Provide a secure application with user registration and authentication using FastAPI and Streamlit.
+ **Functionality**: Allow users to select PDFs, view extracted text, summarize content, and ask questions using OpenAI API.
+ **Deployment**: Ensure secure deployment using Docker and Docker Compose.

**Outcomes**
+ A fully automated pipeline that handles downloading, compressing, and extracting text from PDFs.
+ A client-facing application that enables users to interact with the data securely.
+ Deployment of the application in a containerized environment for ease of use.

## Application Workflow
The application integrates several components, including data acquisition and processing with Airflow, storage on Google Cloud Storage, and a user interface built with Streamlit and FastAPI.

1. **Data Acquisition and Processing (Airflow DAG):**

+ **Task 1** - Web Scraping and PDF Processing:
Fetches PDF file names from the GAIA dataset directories on Hugging Face.
Downloads the PDFs using the Hugging Face API.
Compresses PDFs larger than 4MB using Ghostscript.
Uploads the processed PDFs to the gaia_pdfs folder in Google Cloud Storage (GCS).

+ **Task 2** - Open-Source Text Extraction:
Extracts text, tables, and images (with OCR) from PDFs using tools like pdfplumber, PyMuPDF, and pytesseract.
Saves the extracted content to the opensource_extracted folder in GCS.

+ **Task 3** - Cloudmersive API Text Extraction:
Uses the Cloudmersive API to extract text and perform OCR on images within PDFs.
Saves the extracted content to the cloudmersive_API_extracted folder in GCS.

2. **User Interaction (Frontend and Backend):**

+ **Streamlit Frontend:**
  + Users can register and log in to the application.
  + Allows selection of PDFs and extraction methods.
  + Displays extracted text, summaries, and answers to user questions.

+ **FastAPI Backend:**
  + Handles user authentication and authorization using JWT tokens.
  + Provides API endpoints for file listing, text retrieval, summarization, and Q&A.
  + Interacts with GCS to fetch extracted text files.
  + Utilizes OpenAI API for generating summaries and answering questions.

3. **Backend Processing (FastAPI):**
+ Validates user authentication for secure access for all protected endpoints.
+ Retrieves extracted text based on user selections.
+ Sends prompts to OpenAI API for summarization and question-answering.

4. **Output Delivery:**
+ The Streamlit frontend displays the extracted text, generated summaries, and answers to user queries.
Provides an interactive and user-friendly interface for seamless interaction.

## Project Tree
```.
├── Airflow
│   ├── Dockerfile
│   ├── dags
│   │   ├── Pipeline.py
│   │   ├── task1_Web_Scraping.py
│   │   ├── task2_PDF_Extraction_Opensource.py
│   │   └── task3_PDF_Extraction_Cloudmersive.py
│   ├── docker-compose.yaml
│   └── requirements.txt
├── Extraction_Evaluation
│   ├── Cloudmersive_API_Metrics_Template.ipynb
│   ├── Opensource_Metrics_Template.ipynb
│   └── PDF Extraction API Evaluation.pdf
├── Fast_API
│   ├── Dockerfile
│   └── main.py
├── README.md
├── Streamlit_app
│   ├── Dockerfile
│   └── streamlit_app.py
├── diagrams
│   ├── Assignment2_diagram.ipynb
│   ├── airflow_icon.png
│   ├── docker_icon.png
│   ├── fastapi_icon.png
│   ├── hf_icon.png
│   ├── openai_icon.png
│   ├── pdf_summarizer_and_q&a.png
│   └── streamlit_icon.png
├── docker-compose.yml
└── requirements.txt
```

## Set Up Application Locally
1. Clone the repository to get all the source code on your machine 
```
git clone yourRepo
cd yourRepo
```
2. Set Up Environment Variables at required locations by creating .env files with variable values.
```
#env at Airflow

GOOGLE_APPLICATION_CREDENTIALS=/opt/airflow/"your GCP Service Account json"
AIRFLOW_UID=502
HUGGING_FACE_TOKEN="your huggingface token"
BASE_URL=https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/
TEST_DIRECTORY_URL=https://huggingface.co/datasets/gaia-benchmark/GAIA/tree/main/2023/test
VALIDATION_DIRECTORY_URL=https://huggingface.co/datasets/gaia-benchmark/GAIA/tree/main/2023/validation
TESSERACT_CMD_PATH=/usr/bin/tesseract
CLOUDMERSIVE_API_KEY="your cloudmersive key"

```

3. Build and Run Airflow by running below commands
```
cd Airflow
docker build -t my_airflow_image:latest .
docker-compose up -d
```
Access the Airflow web UI at http://localhost:8080

4. Trigger the Airflow DAG in the Airflow UI (trigger the gaia_processing_dag) to start the data pipeline.

5. Navigate back to root dir to setup relevant env variables for streamlit and FastAPI
```
cd ..
```

```
#env for root dir

DB_HOST="your DB Host"
DB_PORT=5432 # default
DB_NAME=""your DB name
DB_USER="your DB user"
DB_PASSWORD="your DB pwd"

API_URL=http://fastapi:8000

SECRET_KEY="your secret key"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
GOOGLE_APPLICATION_CREDENTIALS="your GCP Service Account json"
OPENAI_API_KEY="your openai API Key"
```

6. Local docker compose build and up, push the images to hub
 + build fastapi and streamlit docker images through docker compose from root dir
 ```
 docker compose build --no-cache
 ```
 + Runs the images thorugh docker compose
 ```
 docker compose up
 ```
 + Tag the FastAPI image:
 ```
 docker tag ImageNameForFastapi Username/ImageNameForFastapi:latest
 ```
 + Tag the Streamlit image:
 ```
 docker tag ImageNameForStreamlit Username/ImageNameForStreamlit:latest
 ```
 + Push FastAPI:
 ```
 docker push Username/ImageNameForFastapi:latest
 ```
 + Push Streamlit:
 ```
 docker push Username/ImageNameForStreamlit:latest
 ```
7. GCP docker setup, create folder, create docker compose file, scp the .env and json file, pull the images, run docker compose.
 + Install Docker:
 ```
 sudo apt update
 sudo apt install -y docker.io
 ```
 + Install Docker Compose:
 ```
 sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
 sudo chmod +x /usr/local/bin/docker-compose
 ```
 + Create a Directory for Your Project:
 ```
 mkdir ~/yourapp
 cd ~/yourapp
 ```
 + scp json file to myapp and .env
 ```
 gcloud compute scp --project YourProjectName --zone YourZone-f /path to your root dir/ServiceAccountJson Username@InstanceName:/PathInGCPToyourapp/ServiceAccountJson
 gcloud compute scp --project YourProject --zone YourZone-f /path to your root dir/.env Username@InstanceName:/PathInGCPToyourapp/.env
 ```
8. nano docker-compose.yml:
```
services:
  fastapi:
    image: Username/ImageNameForFastapi:latest  # Pull from Docker Hub
    container_name: YourFastapiContainer
    ports:
      - "8000:8000"
    env_file:
      - ./.env  # Pass the .env file located in the root directory at runtime
    volumes:
      - ./ServiceAccountJson:/app/ServiceAccountJson  # Mount the JSON file at runtime
    networks:
      - app-network

  streamlit:
    image: Username/ImageNameForStreamlit:latest  # Pull from Docker Hub
    container_name: YourStreamlitContainer
    ports:
      - "8501:8501"
    depends_on:
      - fastapi
    env_file:
      - ./.env  # Pass the .env file located in the root directory at runtime
    volumes:
      - ./ServiceAccountJson:/app/ServiceAccountJson  # Mount the JSON file at runtime
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

9. Pull the Docker images and Start the containers:
```
sudo docker-compose pull
sudo docker-compose up -d
```
 
## Accessing Application via Cloud:
After deploying application through Cloud, you can use the application at url: http://viswanath.me:8501/

