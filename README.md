# Assignment2
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

##Description
This project focuses on automating the extraction of text from PDF files in the GAIA dataset using Apache Airflow and developing a secure, client-facing application using Streamlit and FastAPI. The objectives are to streamline the process of retrieving and processing documents, ensure that the extracted information is accurately populated into data storage, and provide a user-friendly interface for interaction, including functionalities like summarization and question-answering.

Documentation: https://codelabs-preview.appspot.com/?file_id=1QYiFTdbxrUgrE0szRKMQ8sIxHFE_9KpekGauMBp8vzM#0

Demo Video Link: 

##Architecture
![combined_architecture](https://github.com/user-attachments/assets/18f29314-abb7-4e68-ac76-96a83419195b)

##About
Problem
The challenge is to create an automated workflow that extracts text from PDFs in the GAIA Benchmarking Validation & Testing Dataset and to develop a secure, user-friendly application that allows users to interact with the extracted data.

Scope
Automation: Automate the data acquisition and text extraction process for PDFs using Apache Airflow.
User Interaction: Provide a secure application with user registration and authentication using FastAPI and Streamlit.
Functionality: Allow users to select PDFs, view extracted text, summarize content, and ask questions using OpenAI API.
Deployment: Ensure secure deployment and scalability using Docker and Docker Compose.

Outcomes
A fully automated pipeline that handles downloading, compressing, and extracting text from PDFs.
A client-facing application that enables users to interact with the data securely.
Deployment of the application in a containerized environment for scalability and ease of use.

##Application Workflow
The application integrates several components, including data acquisition and processing with Airflow, storage on Google Cloud Storage, and a user interface built with Streamlit and FastAPI.

1. Data Acquisition and Processing (Airflow DAG):
Task 1 - Web Scraping and PDF Processing:

Fetches PDF file names from the GAIA dataset directories on Hugging Face.
Downloads the PDFs using the Hugging Face API.
Compresses PDFs larger than 4MB using Ghostscript.
Uploads the processed PDFs to the gaia_pdfs folder in Google Cloud Storage (GCS).
Task 2 - Open-Source Text Extraction:

Extracts text, tables, and images (with OCR) from PDFs using tools like pdfplumber, PyMuPDF, and pytesseract.
Saves the extracted content to the opensource_extracted folder in GCS.
Task 3 - Cloudmersive API Text Extraction:

Uses the Cloudmersive API to extract text and perform OCR on images within PDFs.
Saves the extracted content to the cloudmersive_API_extracted folder in GCS.
2. User Interaction (Frontend and Backend):
Streamlit Frontend:

Users can register and log in to the application.
Allows selection of PDFs and extraction methods.
Displays extracted text, summaries, and answers to user questions.
FastAPI Backend:

Handles user authentication and authorization using JWT tokens.
Provides API endpoints for file listing, text retrieval, summarization, and Q&A.
Interacts with GCS to fetch extracted text files.
Utilizes OpenAI API for generating summaries and answering questions.
3. Backend Processing (FastAPI):
Validates user authentication for secure access.
Retrieves extracted text based on user selections.
Sends prompts to OpenAI API for summarization and question-answering.
4. Output Delivery:
The Streamlit frontend displays the extracted text, generated summaries, and answers to user queries.
Provides an interactive and user-friendly interface for seamless interaction.

##Project Tree

##Set Up Application Locally
1. Clone the Repository
2. Set Up Environment Variables
3. Build and Run Airflow
4. Trigger the Airflow DAG
5. Build and Run the Application Containers
6. Access the Application at 8501
7. Register and Use the Application

##Accessing Application via Cloud:
After deploying application through Cloud, you can use the application at url: http://viswanath.me:8501/

