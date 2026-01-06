# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for research - copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app

# Ensure bot_logic directory exists
RUN mkdir -p /app/bot_logic

# Expose the port the app runs on
EXPOSE 8000

# Command to run the research environment
CMD ["python", "research/main.py"]