# Use an official lightweight Python runtime
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your web service code
COPY . .

# Expose the port your web service runs on (Render expects a web service)
EXPOSE 8000

# Run your python script (replace qbo_service.py with your exact script name)
CMD ["python", "qbo_service.py"]
