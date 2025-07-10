# Use Python 3.11
FROM python:3.11-slim

# Install Node.js for Irys service
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install Node.js dependencies for Irys
COPY backend/package.json backend/package-lock.json ./
RUN npm install

# Copy backend code
COPY backend/ ./

# Copy frontend build (we'll build it separately)
COPY frontend/build ./static

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]