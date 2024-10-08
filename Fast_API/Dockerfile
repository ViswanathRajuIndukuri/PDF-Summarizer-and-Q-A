# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container to /app
WORKDIR /app

# Copy the entire root directory into /app
COPY . /app

# Install any required packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Expose port 8000 to the outside world
EXPOSE 8000

# Run FastAPI with Uvicorn when the container launches
CMD ["uvicorn", "Fast_API.main:app", "--host", "0.0.0.0", "--port", "8000"]