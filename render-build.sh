#!/bin/bash

# Render Build Script - Builds frontend and prepares for deployment
set -e

echo "🚀 Starting Render build process..."

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd /app/backend
pip install -r requirements.txt

# Install frontend dependencies and build
echo "📦 Installing frontend dependencies..."
cd /app/frontend
yarn install

# Build frontend with environment variables
echo "🔨 Building frontend..."
export REACT_APP_BACKEND_URL=https://notion-web3.onrender.com
export REACT_APP_IRYS_NETWORK=devnet
export REACT_APP_IRYS_RPC_URL=https://rpc.sepolia.org
yarn build

# Copy built files to backend static directory
echo "📁 Copying built files to backend..."
cd /app
mkdir -p backend/static
cp -r frontend/build/* backend/static/

echo "✅ Build complete! Ready for deployment."