# Multi-stage build for React frontend + FastAPI backend

# Stage 1: Build React frontend
FROM node:20 as frontend

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
COPY frontend/yarn.lock ./
RUN yarn install

# Copy frontend source and build
COPY frontend/ ./
RUN yarn build

# Stage 2: Backend with built frontend
FROM python:3.11-slim

WORKDIR /app

# Install Node.js v20 for Irys service
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip cache purge

# Copy and install Node.js dependencies for Irys
COPY backend/package.json backend/package-lock.json ./
RUN npm install
RUN npm prune --production

# Copy backend code
COPY backend/ ./

# Copy built frontend from stage 1
COPY --from=frontend /app/frontend/build ./static

# Set default port for Render
ENV PORT=8000

# Expose port
EXPOSE 8000

# Start command with dynamic port support
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]