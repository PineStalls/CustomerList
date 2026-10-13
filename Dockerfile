# Use a standard Python runtime
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first to speed up builds
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy EVERY file from your local directory into the container's /app directory
COPY . /app/

# Expose port for Render
EXPOSE 8000

# Start the application (Make sure this matches your exact filename)
CMD ["python", "/app/qbo_service.py"]
