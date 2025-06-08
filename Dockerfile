# Use an official Python slim image as a base
FROM python:3.13.4-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the source code
COPY . .

# Set working directory to src
WORKDIR /app/src

# Expose port(s)
EXPOSE 7860

# Create and use a non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Set the default command to run your app
CMD ["python", "main.py"]
