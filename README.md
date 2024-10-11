# PDF Summarizer and Q&A
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

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

**Demo Video Link**:

**Application URL**: http://viswanath.me:8501/

## Architecture
![combined_architecture](https://github.com/user-attachments/assets/18f29314-abb7-4e68-ac76-96a83419195b)

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
```
.
├── Airflow
│   ├── Dockerfile
│   ├── bigdata-8989-c84dd170777d.json
│   ├── config
│   ├── dags
│   │   ├── Pipeline.py
│   │   ├── __pycache__
│   │   ├── task1_Web_Scraping.py
│   │   ├── task2_PDF_Extraction_Opensource.py
│   │   └── task3_PDF_Extraction_Cloudmersive.py
│   ├── docker-compose.yaml
│   ├── plugins
│   └── requirements.txt
├── Fast_API
│   ├── Dockerfile
│   └── main.py
├── README.md
├── Streamlit_app
│   ├── Dockerfile
│   └── streamlit_app.py
├── docker-compose.yml
├── requirements.txt
└── venv
```

## Set Up Application Locally
1. Clone the repository to get all the source code on your machine 
```
git clone yourRepo
cd yourRepo
```
2. Set Up Environment Variables at required locations by creating .env files with variable values.

3. Build and Run Airflow by ruuning below commands
```
cd Airflow
docker build -t my_airflow_image:latest .
docker-compose up -d
```
Access the Airflow web UI at http://localhost:8080

4. Trigger the Airflow DAG in the Airflow UI (trigger the gaia_processing_dag) to start the data pipeline.

5. Build and Run the Application Containers
```
cd .. #Navigating back to root dir
docker-compose up --build #Build and run the FastAPI and Streamlit containers using Docker Compose
```

6. Access the Application by opening a web browser and navigate to http://localhost:8501

7. Now you'll see the application running, Register a new user and Login to access all the functionalities of the application.

## Accessing Application via Cloud:
After deploying application through Cloud, you can use the application at url: http://viswanath.me:8501/

