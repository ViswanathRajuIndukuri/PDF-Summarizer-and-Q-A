FROM apache/airflow:2.10.2

USER root

# Install system-level dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    ghostscript \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python packages
#COPY requirements.txt /tmp/
#RUN pip install --no-cache-dir -r /tmp/requirements.txt
