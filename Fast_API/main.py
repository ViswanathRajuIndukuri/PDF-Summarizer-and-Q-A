from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from psycopg2 import connect, sql, OperationalError, errors
from uuid import uuid4, UUID
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List

# Import Google Cloud Storage and exceptions
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Google Cloud Storage client
storage_client = storage.Client()

# Database connection dependency with error handling
def get_db_connection():
    try:
        conn = connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except OperationalError as e:
        raise HTTPException(status_code=500, detail="Database connection error")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models with input validation
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3 or len(v) > 30:
            raise ValueError('Username must be between 3 and 30 characters')
        return v

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class SummarizeRequest(BaseModel):
    file_name: str
    source_type: str  # 'opensource' or 'cloudmersive_API'

class QuestionRequest(BaseModel):
    file_name: str
    source_type: str  # 'opensource' or 'cloudmersive_API'
    question: str

CREATE_USERS_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

# Initialize the database
@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_USERS_TABLE_QUERY)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error initializing database: {e}")
    finally:
        cur.close()
        conn.close()

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, hashed_password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user and verify_password(password, user[1]):
            return {"id": user[0], "username": username}
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error during authentication")
    finally:
        cur.close()
        conn.close()


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=320))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# User registration endpoint with error handling
@app.post("/register", response_model=UserOut)
def register_user(user: UserCreate):
    try:
        hashed_password = hash_password(user.password)
        user_id = uuid4()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (id, email, username, hashed_password) VALUES (%s, %s, %s, %s) RETURNING created_at",
            (str(user_id), user.email, user.username, hashed_password))
        created_at = cur.fetchone()[0]
        conn.commit()
        return {"id": user_id, "email": user.email, "username": user.username, "created_at": created_at}
    except errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Email or username already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error during registration")
    finally:
        cur.close()
        conn.close()

# Login endpoint with error handling
@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not form_data.username or not form_data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user['username']}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoint with enhanced error handling
@app.get("/users/me", response_model=UserOut)
async def read_user_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, email, username, created_at FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": UUID(user[0]), "email": user[1], "username": user[2], "created_at": user[3]}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving user information")
    finally:
        cur.close()
        conn.close()

# List Files Endpoint
@app.get("/files", response_model=List[str])
async def list_files(
    token: str = Depends(oauth2_scheme)
):
    # Verify the token and get the current user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # List files in the 'gaia_pdfs' folder of the 'gaia_files_pdf' bucket
    try:
        bucket_name = 'gaia_files_pdf'
        prefix = 'gaia_pdfs/'  # Folder containing the PDF files
        bucket = storage_client.get_bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        file_names = [blob.name.replace(prefix, '') for blob in blobs if not blob.name.endswith('/')]
        return file_names
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

# Get Extracted Text Endpoint
@app.get("/get-extracted-text")
async def get_extracted_text(
    file_name: str = Query(...),
    source_type: str = Query(...),  # 'opensource' or 'cloudmersive_API'
    token: str = Depends(oauth2_scheme)
):
    # Verify the token and get the current user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Validate source_type input
    if source_type not in ["opensource", "cloudmersive_API"]:
        raise HTTPException(status_code=400, detail="source_type must be 'opensource' or 'cloudmersive_API'")

    # Map source_type to the correct folder path
    def get_file_prefix(source_type: str) -> str:
        if source_type == 'opensource':
            return "opensource_extracted/"
        elif source_type == 'cloudmersive_API':
            return "cloudmersive_API_extracted/"
        else:
            raise ValueError('Invalid source_type')

    # Construct the full blob name
    prefix = get_file_prefix(source_type)
    # Replace the file extension with .txt
    base_name, _ = os.path.splitext(file_name)
    txt_file_name = base_name + '.txt'
    blob_name = prefix + txt_file_name

    # Retrieve the content of the .txt file from the bucket
    try:
        bucket_name = 'gaia_files_pdf'
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        text_content = blob.download_as_text()
        return {"extracted_text": text_content}
    except NotFound:
        raise HTTPException(status_code=404, detail="Extracted text file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extracted text: {str(e)}")

# Helper function to retrieve extracted text content
def get_extracted_text_content(file_name: str, source_type: str) -> str:
    # Map source_type to the correct folder path
    def get_file_prefix(source_type: str) -> str:
        if source_type == 'opensource':
            return "opensource_extracted/"
        elif source_type == 'cloudmersive_API':
            return "cloudmersive_API_extracted/"
        else:
            raise ValueError('Invalid source_type')

    # Construct the full blob name
    prefix = get_file_prefix(source_type)
    # Replace the file extension with .txt
    base_name, _ = os.path.splitext(file_name)
    txt_file_name = base_name + '.txt'
    blob_name = prefix + txt_file_name

    # Retrieve the content of the .txt file from the bucket
    try:
        bucket_name = 'gaia_files_pdf'
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        text_content = blob.download_as_text()
        return text_content
    except NotFound:
        raise HTTPException(status_code=404, detail="Extracted text file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extracted text: {str(e)}")

# Summarize Endpoint
@app.post("/summarize")
async def summarize_pdf(
    request: SummarizeRequest,
    token: str = Depends(oauth2_scheme)
):
    # Token verification (same as before)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Validate source_type input
    if request.source_type not in ["opensource", "cloudmersive_API"]:
        raise HTTPException(status_code=400, detail="source_type must be 'opensource' or 'cloudmersive_API'")

    # Retrieve the extracted text
    text_content = get_extracted_text_content(request.file_name, request.source_type)

    # Prepare the prompt for summarization
    prompt = f"Please provide a concise and comprehensive summary of the following text:\n\n{text_content}"

    # Send the prompt to OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Replace with a valid model name if necessary
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes texts."},
                {"role": "user", "content": prompt}
            ]
        )
        message = response.choices[0].message.content
        return {"summary": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with OpenAI API: {str(e)}")

# Ask Question Endpoint
@app.post("/ask-question")
async def ask_question(
    request: QuestionRequest,
    token: str = Depends(oauth2_scheme)
):
    # Token verification (same as before)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Validate source_type input
    if request.source_type not in ["opensource", "cloudmersive_API"]:
        raise HTTPException(status_code=400, detail="source_type must be 'opensource' or 'cloudmersive_API'")

    # Retrieve the extracted text
    text_content = get_extracted_text_content(request.file_name, request.source_type)

    # Prepare the prompt for question-answering
    prompt = f"The following text is from a PDF document:\n\n{text_content}\n\nAnswer the following question based on the text above:\n{request.question}"

    # Send the prompt to OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Replace with a valid model name if necessary
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided text."},
                {"role": "user", "content": prompt}
            ]
        )
        message = response.choices[0].message.content
        return {"answer": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with OpenAI API: {str(e)}")