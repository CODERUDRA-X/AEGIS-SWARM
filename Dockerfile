# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Hugging Face requires specific folder permissions to save files
RUN mkdir -p temp_uploads && chmod 777 temp_uploads

# Hugging Face Spaces strictly uses port 7860
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]