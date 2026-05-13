# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP run.py

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    iperf3 \
    gcc \
    libmariadb-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose ports: 5000 (Flask), 5201 (Iperf3 default)
EXPOSE 5000 5201

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
