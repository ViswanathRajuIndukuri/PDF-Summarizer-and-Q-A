# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container to /app
WORKDIR /app

# Copy the entire root directory into /app
COPY . /app

# Install any required packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Expose port 8501 for Streamlit
EXPOSE 8501

# Run Streamlit when the container launches
CMD ["streamlit", "run", "Streamlit_app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]