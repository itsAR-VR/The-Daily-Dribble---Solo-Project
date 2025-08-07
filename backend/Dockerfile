# Use a proven base image with Chrome already installed
FROM browserless/chrome:latest

# Install Python 3.11
USER root
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create and use virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the backend source so imports resolve from /app
COPY backend/ .

# Create jobs directory
RUN mkdir -p jobs

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome

# Ensure Python can import from /app
ENV PYTHONPATH=/app

# Expose port
EXPOSE $PORT

# Start command
CMD uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT 