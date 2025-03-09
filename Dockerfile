FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Create directories for data
RUN mkdir -p /app/scrapers_output /app/processed_output /app/models

# Copy the code
COPY scripts /app/scripts
COPY SA_LEGAL_LLM_CHECKLIST.md /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Command to run when container starts
ENTRYPOINT ["python", "scripts/process_legal_documents.py"]
CMD ["--help"] 