# Use the official Python 3.10 slim image
FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code into /app
COPY . .

# Expose the port
EXPOSE $PORT

# Run Uvicorn from /app
CMD uvicorn store:app --host 0.0.0.0 --port ${PORT:-8080}