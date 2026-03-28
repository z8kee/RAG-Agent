# Use Python 3.11 slim image for a smaller footprint
FROM python:3.11-slim

# Install ffmpeg (Required for OpenAI Whisper to process audio)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory to the project root
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Change working directory to scripts so local imports work natively
WORKDIR /app/scripts

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the unified FastAPI backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]