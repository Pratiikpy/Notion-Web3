# Irys Snippet Vault - Social Digital Content Platform

A Web3 social platform for sharing and discovering digital content (snippets, poetry, images) stored on the Irys blockchain with AI-powered analysis.

## Features

- **Multi-Content Types**: Web snippets, text/poetry, images
- **AI Analysis**: Claude AI-powered mood and theme detection
- **Social Features**: Follow system, likes, comments, user discovery
- **Blockchain Storage**: Irys blockchain for permanent content storage
- **Real-time Feed**: Public content feed with social interactions

## Render Deployment Guide

### One-time Render Setup

1. **Create Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect this repository
   - Select "Free" plan

2. **Environment Variables**
   Add these environment variables in Render:
   - `MONGO_URL`: Your MongoDB Atlas connection string
   - `IRYS_PRIVATE_KEY`: Wallet private key for Irys blockchain storage
   - `ANTHROPIC_API_KEY`: Claude AI API key for content analysis
   - `DB_NAME`: MongoDB database name
   - ⚠️ **Important**: Do NOT set `PORT` manually - Render sets this automatically

3. **Deploy**
   - Click "Deploy" button
   - **Multi-stage build**: Frontend is built automatically using Node.js, then served by FastAPI
   - First build takes approximately 3-5 minutes (includes React build)
   - Wait for deployment to complete

4. **Update CORS Settings**
   - After deployment is live, copy your Render URL (e.g., `https://your-service.onrender.com`)
   - Replace `YOUR-SERVICE` in `/app/backend/server.py` line 36 with your actual service name
   - Example: `"https://my-irys-app.onrender.com"`
   - Commit and push this change

5. **Static File Serving**
   - ✅ Already configured: Multi-stage Docker build creates and serves React build files
   - The root route (`/`) serves the React app with SPA routing support
   - Static assets are served from `/static` path

### Required API Keys

Before deploying, ensure you have:

1. **MongoDB Atlas**: Create a free cluster at mongodb.com
2. **Anthropic API**: Get Claude API key from console.anthropic.com
3. **Irys Wallet**: Generate a private key for blockchain storage

### Local Development

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
yarn install

# Build frontend
yarn build

# Start development server
cd ../backend
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Environment Variables Reference

```env
# Database
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname
DB_NAME=irys_vault

# AI Services
ANTHROPIC_API_KEY=your_claude_api_key_here

# Blockchain
IRYS_PRIVATE_KEY=your_wallet_private_key_here

# Deployment (Render sets automatically)
PORT=8000
```

## Architecture

- **Backend**: FastAPI with MongoDB
- **Frontend**: React with Tailwind CSS
- **AI**: Claude AI for content analysis
- **Blockchain**: Irys for permanent storage
- **Deployment**: Render-optimized with dynamic port support
