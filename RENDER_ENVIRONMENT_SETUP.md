# Render Environment Variables Setup Guide

## Required Environment Variables for Render Deployment

Please add the following environment variables in your **Render Dashboard** -> **Web Service Settings** -> **Environment Variables**:

### 1. Database Configuration
```
MONGO_URL=mongodb+srv://apkados:IGaA3lPmmhiSVRFacluster0.rbnfgn0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&ssl=true&tlsAllowInvalidCertificates=true
DB_NAME=sample_mflix
```

### 2. AI Integration (Claude API) - **FIXED**
```
CLAUDE_API_KEY=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
```

### 3. Blockchain Integration (Irys)
```
IRYS_PRIVATE_KEY=0x725bbe9ad10ef6b48397d37501ff0c908119fdc0513a85a046884fc9157c80f5
```

### 4. Server Configuration
```
PORT=8000
```

### 5. Frontend Configuration (Build-time)
```
REACT_APP_BACKEND_URL=https://notion-web3.onrender.com
REACT_APP_IRYS_NETWORK=devnet
REACT_APP_IRYS_RPC_URL=https://rpc.sepolia.org
```

## How to Add Environment Variables in Render:

1. Go to your Render Dashboard
2. Click on your Web Service
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Add each variable with the **exact names and values** above
6. Click **Save Changes**

## Build Script for Render:

Make sure your Render service is configured with:
- **Build Command**: `./render-build.sh`
- **Start Command**: `cd backend && python server.py`

## Verification Steps:

After adding the environment variables and redeploying:

1. Check that the app loads at `https://notion-web3.onrender.com`
2. Test profile editing functionality
3. Test snippet extraction
4. Test AI features (should now work with Claude API)
5. Test image upload
6. Test social features

## Notes:

- The **CLAUDE_API_KEY** will now work correctly with the Claude API
- The **double /api/ prefix issue** has been fixed in the frontend
- All environment variables are properly configured for production

Your app should now be fully functional on Render!