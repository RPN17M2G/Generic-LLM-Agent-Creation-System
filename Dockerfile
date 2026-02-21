FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variable to disable NumPy CPU feature checks
ENV NPY_DISABLE_CPU_FEATURES="X86_V2"

# Copy requirements first for better caching
COPY requirements.txt .

# Install NumPy first with a compatible version (before pandas)
RUN pip install --no-cache-dir "numpy<2.0"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=api/app.py
ENV FLASK_ENV=production

# Run Flask app
CMD ["python", "api/app.py"]

