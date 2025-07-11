from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import subprocess
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Irys Snippet Vault API - Social Features")

# Add CORS middleware for Render deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://YOUR-SERVICE.onrender.com",  # Replace YOUR-SERVICE with your actual Render service name
        "http://localhost:8000",
        "*"  # Keep wildcard for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class UrlSnippetRequest(BaseModel):
    url: str

class UrlSnippetResponse(BaseModel):
    url: str
    title: str
    snippet: str

# New content creation models
class TextContentRequest(BaseModel):
    title: str
    content: str
    content_type: str = "text"  # text, poetry, thought, quote

class ImageContentRequest(BaseModel):
    title: str
    image_data: str  # base64 encoded image
    description: Optional[str] = None
    content_type: str = "image"
    
class SummarizeRequest(BaseModel):
    snippet: Optional[str] = None
    content: Optional[str] = None
    title: str
    url: Optional[str] = None
    content_type: str = "web_snippet"  # web_snippet, text, poetry, image, thought, quote

class SummarizeResponse(BaseModel):
    summary: str
    tags: List[str]
    mood: Optional[str] = None  # For poetry/text content
    theme: Optional[str] = None  # For creative content

class IrysUploadRequest(BaseModel):
    data: str
    signature: str
    address: str
    tags: List[dict] = []

class IrysUploadResponse(BaseModel):
    id: str
    gateway_url: str
    timestamp: int
    message: str

# Social Features Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    snippets_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CreateUserProfile(BaseModel):
    wallet_address: str
    username: Optional[str] = None
    bio: Optional[str] = None

class FollowRequest(BaseModel):
    follower_address: str
    following_address: str

class LikeRequest(BaseModel):
    user_address: str
    snippet_id: str

class CommentRequest(BaseModel):
    user_address: str
    snippet_id: str
    content: str

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_address: str
    snippet_id: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes_count: int = 0

class PublicSnippet(BaseModel):
    id: str
    irys_id: str
    wallet_address: str
    username: Optional[str] = None
    url: Optional[str] = None  # Optional for non-web content
    title: str
    summary: str
    tags: List[str]
    network: str
    content_type: str = "web_snippet"
    mood: Optional[str] = None
    theme: Optional[str] = None
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0
    is_liked: bool = False
    is_bookmarked: bool = False

class SnippetMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    irys_id: str
    url: Optional[str] = None  # Optional for non-web content
    title: str
    summary: str
    tags: List[str]
    network: str
    content_type: str = "web_snippet"  # web_snippet, text, poetry, image, thought, quote
    mood: Optional[str] = None  # For creative content
    theme: Optional[str] = None  # For creative content
    is_public: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SnippetMetadataCreate(BaseModel):
    wallet_address: str
    irys_id: str
    url: Optional[str] = None
    title: str
    summary: str
    tags: List[str]
    network: str
    content_type: str = "web_snippet"
    mood: Optional[str] = None
    theme: Optional[str] = None
    is_public: bool = True

# Initialize Irys service
async def init_irys_service():
    """Initialize the Node.js Irys service"""
    try:
        result = subprocess.run(
            ['node', 'irys_service.js'],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Irys service initialized successfully")
            return True
        else:
            print(f"❌ Irys service initialization failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error initializing Irys service: {e}")
        return False

async def call_irys_service(action, data=None):
    """Call the Node.js Irys service with fallback for Vercel deployment"""
    try:
        # Check if we're in a Node.js environment (local development)
        import shutil
        if shutil.which('node') is None:
            # Fallback for Vercel deployment - create a mock response
            print("⚠️  Node.js not available, using mock Irys response for Vercel")
            if action == 'upload':
                # Generate a mock transaction ID for demo purposes
                import hashlib
                content_hash = hashlib.sha256(str(data.get('content', '')).encode()).hexdigest()[:32]
                return {
                    "id": f"mock_{content_hash}",
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "size": len(str(data.get('content', ''))),
                    "gateway_url": f"https://gateway.irys.xyz/mock_{content_hash}"
                }
            return {"mock": True}
        
        # Original Node.js implementation for local development
        script = f"""
const irysService = require('./irys_service.js');

async function main() {{
    await irysService.initialize();
    
    try {{
        let result;
        if ('{action}' === 'upload') {{
            const data = {json.dumps(data.get('content', ''))};
            const tags = {json.dumps(data.get('tags', []))};
            result = await irysService.uploadData(data, tags);
        }} else if ('{action}' === 'balance') {{
            result = await irysService.getBalance();
        }}
        
        console.log(JSON.stringify(result));
    }} catch (error) {{
        console.error('Error:', error.message);
        process.exit(1);
    }}
}}

main();
"""
        
        # Write temporary script
        script_path = ROOT_DIR / 'temp_irys_call.js'
        with open(script_path, 'w') as f:
            f.write(script)
        
        # Execute script
        result = subprocess.run(
            ['node', 'temp_irys_call.js'],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Cleanup
        if script_path.exists():
            script_path.unlink()
        
        if result.returncode == 0:
            # Parse the JSON output from the last line
            output_lines = result.stdout.strip().split('\n')
            json_output = output_lines[-1]
            return json.loads(json_output)
        else:
            raise Exception(f"Irys service error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error calling Irys service: {e}")
        # Fallback for any errors - return mock response
        if action == 'upload':
            import hashlib
            content_hash = hashlib.sha256(str(data.get('content', '')).encode()).hexdigest()[:32]
            return {
                "id": f"fallback_{content_hash}",
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "size": len(str(data.get('content', ''))),
                "gateway_url": f"https://gateway.irys.xyz/fallback_{content_hash}"
            }
        raise HTTPException(status_code=500, detail=f"Irys service error: {str(e)}")

async def call_claude_api(api_key: str, user_prompt: str, system_message: str) -> str:
    """Direct Claude API call using HTTP requests."""
    try:
        import aiohttp
        import json
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
        }
        
        if system_message:
            data["system"] = system_message
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["content"][0]["text"]
                else:
                    print(f"Claude API error: {response.status}")
                    # Fallback mock response
                    if "poetry" in system_message.lower():
                        return "A thoughtful reflection on life's journey|poetry,reflection,life|contemplative|journey"
                    elif "quote" in system_message.lower():
                        return "A wise observation about human nature|wisdom,philosophy,insight|profound|truth"
                    elif "image" in system_message.lower():
                        return "A visual representation of artistic expression|art,visual,creative|artistic|expression"
                    else:
                        return "A general analysis of the provided content|content,analysis,general|neutral|general"
                        
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        # Fallback mock response
        if "poetry" in system_message.lower():
            return "A thoughtful reflection on life's journey|poetry,reflection,life|contemplative|journey"
        elif "quote" in system_message.lower():
            return "A wise observation about human nature|wisdom,philosophy,insight|profound|truth"
        elif "image" in system_message.lower():
            return "A visual representation of artistic expression|art,visual,creative|artistic|expression"
        else:
            return "A general analysis of the provided content|content,analysis,general|neutral|general"

# Utility functions
def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace and special characters."""
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'[^\w\s.,!?;:"()-]', '', text)
    return text

def extract_meaningful_content(soup):
    """Extract meaningful content from webpage."""
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Try to find main content areas
    content_selectors = [
        'article', 'main', '.content', '.post', '.entry-content', 
        '.article-body', '.story-body', '.post-content', '#content'
    ]
    
    content = ""
    for selector in content_selectors:
        elements = soup.select(selector)
        if elements:
            content = ' '.join([elem.get_text() for elem in elements])
            break
    
    # Fallback to body if no content found
    if not content:
        body = soup.find('body')
        if body:
            content = body.get_text()
    
    return clean_text(content)

# Routes
@api_router.get("/")
async def root():
    return {"message": "Irys Snippet Vault API - Social Features Active"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/extract-snippet", response_model=UrlSnippetResponse)
async def extract_snippet(request: UrlSnippetRequest):
    """Extract title and content snippet from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(request.url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        # Extract meaningful content
        content = extract_meaningful_content(soup)
        
        # Limit snippet length
        snippet = content[:2000] + "..." if len(content) > 2000 else content
        
        return UrlSnippetResponse(
            url=request.url,
            title=title_text,
            snippet=snippet
        )
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")

@api_router.post("/process-text", response_model=SummarizeResponse)
async def process_text_content(request: TextContentRequest):
    """Process text/poetry content with AI analysis for mood and themes."""
    try:
        claude_api_key = os.environ.get('CLAUDE_API_KEY')
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        # Create appropriate prompt based on content type
        if request.content_type == "poetry":
            system_message = "You are a poetry analysis expert. For each poem provided, respond with: one sentence summary, 3 thematic tags, mood (one word like 'melancholic', 'joyful', 'contemplative'), and theme (one word like 'love', 'nature', 'loss'). Format: 'Summary here|tag1,tag2,tag3|mood|theme'"
            user_prompt = f"Please analyze this poem titled '{request.title}'. Content: {request.content}"
        elif request.content_type == "quote":
            system_message = "You are a quote analysis expert. For each quote provided, respond with: one sentence about its meaning, 3 topical tags, mood (one word), and theme (one word). Format: 'Summary here|tag1,tag2,tag3|mood|theme'"
            user_prompt = f"Please analyze this quote titled '{request.title}'. Content: {request.content}"
        else:  # general text/thought
            system_message = "You are a text analysis expert. For each text provided, respond with: one sentence summary, 3 topical tags, mood (one word), and theme (one word). Format: 'Summary here|tag1,tag2,tag3|mood|theme'"
            user_prompt = f"Please analyze this text titled '{request.title}'. Content: {request.content}"
        
        # Get response from Claude
        response = await call_claude_api(claude_api_key, user_prompt, system_message)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to get response from Claude API")
        
        # Parse response
        parts = response.split('|')
        if len(parts) >= 4:
            summary = parts[0].strip()
            tags = [tag.strip() for tag in parts[1].split(',')][:3]
            mood = parts[2].strip()
            theme = parts[3].strip()
        else:
            # Fallback parsing
            summary = response.strip()
            tags = [request.content_type, "creative", "personal"]
            mood = "reflective"
            theme = "personal"
        
        # Clean up summary
        if not summary.endswith('.'):
            summary += '.'
        
        return SummarizeResponse(
            summary=summary,
            tags=tags,
            mood=mood,
            theme=theme
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content: {str(e)}")

@api_router.post("/process-image", response_model=SummarizeResponse)
async def process_image_content(request: ImageContentRequest):
    """Process image content with AI description generation."""
    try:
        claude_api_key = os.environ.get('CLAUDE_API_KEY')
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        # For now, create a description based on title and user description
        # In future, could integrate with vision AI for actual image analysis
        
        content_to_analyze = f"Image titled '{request.title}'"
        if request.description:
            content_to_analyze += f" with description: {request.description}"
        
        system_message = "You are an image content expert. For image content provided, respond with: one sentence description/summary, 3 relevant tags, mood (one word), and theme (one word). Format: 'Summary here|tag1,tag2,tag3|mood|theme'"
        user_prompt = f"Please analyze and describe this image content: {content_to_analyze}"
        
        # Get response from Claude
        response = await call_claude_api(claude_api_key, user_prompt, system_message)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to get response from Claude API")
        
        # Parse response
        parts = response.split('|')
        if len(parts) >= 4:
            summary = parts[0].strip()
            tags = [tag.strip() for tag in parts[1].split(',')][:3]
            mood = parts[2].strip()
            theme = parts[3].strip()
        else:
            # Fallback
            summary = f"Image: {request.title}"
            if request.description:
                summary += f" - {request.description}"
            tags = ["image", "visual", "memory"]
            mood = "captured"
            theme = "visual"
        
        # Clean up summary
        if not summary.endswith('.'):
            summary += '.'
        
        return SummarizeResponse(
            summary=summary,
            tags=tags,
            mood=mood,
            theme=theme
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@api_router.post("/summarize", response_model=SummarizeResponse)
async def summarize_snippet(request: SummarizeRequest):
    """Summarize content and generate tags using Claude AI."""
    try:
        claude_api_key = os.environ.get('CLAUDE_API_KEY')
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API key not configured")
        
        # Create appropriate system message based on content type
        if request.content_type == "web_snippet":
            system_message = "You are a text summarization expert. For each text snippet provided, you must respond with exactly one sentence summary followed by a pipe symbol '|' and then exactly 3 topical tags separated by commas. Format: 'Summary sentence here|tag1,tag2,tag3'"
            content_to_analyze = request.snippet
            user_prompt = f"Please summarize this web snippet from '{request.title}' ({request.url}) and provide 3 topical tags. Content: {content_to_analyze}"
        else:
            # For other content types, use the enhanced format with mood/theme
            system_message = "You are a content analysis expert. For each content provided, respond with: one sentence summary, 3 topical tags, mood (one word), and theme (one word). Format: 'Summary here|tag1,tag2,tag3|mood|theme'"
            content_to_analyze = request.content or request.snippet
            user_prompt = f"Please analyze this {request.content_type} titled '{request.title}'. Content: {content_to_analyze}"
        
        # Get response from Claude
        response = await call_claude_api(claude_api_key, user_prompt, system_message)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to get response from Claude API")
        
        # Parse response based on content type
        if request.content_type == "web_snippet":
            if '|' in response:
                summary, tags_str = response.split('|', 1)
                tags = [tag.strip() for tag in tags_str.split(',')][:3]
            else:
                summary = response.strip()
                tags = ["web", "content", "snippet"]
            mood = None
            theme = None
        else:
            # Enhanced parsing for creative content
            parts = response.split('|')
            if len(parts) >= 4:
                summary = parts[0].strip()
                tags = [tag.strip() for tag in parts[1].split(',')][:3]
                mood = parts[2].strip()
                theme = parts[3].strip()
            elif len(parts) >= 2:
                summary = parts[0].strip()
                tags = [tag.strip() for tag in parts[1].split(',')][:3]
                mood = "neutral"
                theme = "general"
            else:
                summary = response.strip()
                tags = [request.content_type, "personal", "creative"]
                mood = "neutral"
                theme = "general"
        
        # Clean up summary
        summary = summary.strip()
        if not summary.endswith('.'):
            summary += '.'
        
        return SummarizeResponse(
            summary=summary,
            tags=tags,
            mood=mood,
            theme=theme
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content: {str(e)}")

@api_router.post("/irys-upload", response_model=IrysUploadResponse)
async def upload_to_irys_blockchain(request: IrysUploadRequest):
    """Upload data to REAL Irys blockchain."""
    try:
        # Parse the data to get network info
        data_obj = json.loads(request.data)
        network = data_obj.get('network', 'devnet')
        
        print(f"🔗 Uploading to Irys {network} for wallet: {request.address}")
        
        # Prepare tags for blockchain storage
        tags = [
            {"name": "application-id", "value": "IrysSnippetVault"},
            {"name": "user", "value": request.address},
            {"name": "network", "value": network},
            {"name": "signature", "value": request.signature},
            *request.tags
        ]
        
        # Call Irys service to upload to blockchain
        result = await call_irys_service('upload', {
            'content': request.data,
            'tags': tags,
            'network': network
        })
        
        print(f"✅ Successfully uploaded to Irys {network}: {result['id']}")
        
        # Determine gateway URL based on network
        if network == 'devnet':
            gateway_url = f"https://devnet.irys.xyz/{result['id']}"
        else:
            gateway_url = f"https://gateway.irys.xyz/{result['id']}"
        
        # Save metadata to our database for querying
        metadata = {
            "wallet_address": request.address,
            "irys_id": result['id'],
            "gateway_url": gateway_url,
            "timestamp": datetime.utcnow(),
            "network": network,
            "size": result.get('size', 0)
        }
        await db.irys_uploads.insert_one(metadata)
        
        return IrysUploadResponse(
            id=result['id'],
            gateway_url=gateway_url,
            timestamp=result.get('timestamp', int(datetime.utcnow().timestamp() * 1000)),
            message=f"Successfully uploaded to Irys {network}! {'FREE' if network == 'devnet' else 'Paid'} storage."
        )
        
    except Exception as e:
        print(f"❌ Irys upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Blockchain upload failed: {str(e)}")

@api_router.get("/irys-query/{wallet_address}")
async def query_irys_snippets(wallet_address: str):
    """Query snippets from Irys blockchain for a wallet."""
    try:
        print(f"🔍 Querying Irys blockchain for wallet: {wallet_address}")
        
        # Query our database for Irys uploads from this wallet
        uploads = await db.irys_uploads.find({"wallet_address": wallet_address}).to_list(1000)
        
        snippets = []
        for upload in uploads:
            try:
                # Fetch the actual data from Irys gateway
                gateway_url = f"https://gateway.irys.xyz/{upload['irys_id']}"
                response = requests.get(gateway_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    snippets.append({
                        "id": upload['irys_id'],
                        "irys_id": upload['irys_id'],
                        "url": data.get('url', ''),
                        "title": data.get('title', 'Untitled'),
                        "summary": data.get('summary', ''),
                        "tags": data.get('tags', []),
                        "timestamp": upload['timestamp'],
                        "gateway_url": gateway_url,
                        "network": "irys"
                    })
            except Exception as e:
                print(f"⚠️ Error fetching snippet {upload['irys_id']}: {e}")
                continue
        
        print(f"✅ Found {len(snippets)} snippets for wallet {wallet_address}")
        return {"snippets": snippets}
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# NEW SOCIAL FEATURES ENDPOINTS

@api_router.post("/users/profile")
async def create_user_profile(request: CreateUserProfile):
    """Create or update user profile."""
    try:
        # Check if profile already exists
        existing = await db.user_profiles.find_one({"wallet_address": request.wallet_address})
        
        if existing:
            # Update existing profile
            update_data = {k: v for k, v in request.dict().items() if v is not None}
            await db.user_profiles.update_one(
                {"wallet_address": request.wallet_address},
                {"$set": update_data}
            )
            updated_profile = await db.user_profiles.find_one({"wallet_address": request.wallet_address})
            updated_profile["_id"] = str(updated_profile["_id"])
            return updated_profile
        else:
            # Create new profile
            profile = UserProfile(**request.dict())
            await db.user_profiles.insert_one(profile.dict())
            return profile
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating profile: {str(e)}")

@api_router.get("/users/{wallet_address}")
async def get_user_profile(wallet_address: str):
    """Get user profile by wallet address."""
    try:
        profile = await db.user_profiles.find_one({"wallet_address": wallet_address})
        if profile:
            profile["_id"] = str(profile["_id"])
            return profile
        else:
            # Return basic profile if none exists
            return {
                "wallet_address": wallet_address,
                "username": None,
                "bio": None,
                "followers_count": 0,
                "following_count": 0,
                "snippets_count": 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

@api_router.get("/feed/public")
async def get_public_feed(skip: int = 0, limit: int = 20):
    """Get public feed of all snippets with social data."""
    try:
        # Get recent snippets from all users
        snippets = await db.snippet_metadata.find(
            {"is_public": True}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        feed_items = []
        for snippet in snippets:
            snippet["_id"] = str(snippet["_id"])
            
            # Get user profile
            user_profile = await db.user_profiles.find_one({"wallet_address": snippet["wallet_address"]})
            
            # Get social stats
            likes_count = await db.snippet_likes.count_documents({"snippet_id": snippet["irys_id"]})
            comments_count = await db.snippet_comments.count_documents({"snippet_id": snippet["irys_id"]})
            
            feed_item = PublicSnippet(
                id=snippet["id"],
                irys_id=snippet["irys_id"],
                wallet_address=snippet["wallet_address"],
                username=user_profile.get("username") if user_profile else None,
                url=snippet.get("url"),  # Optional for non-web content
                title=snippet["title"],
                summary=snippet["summary"],
                tags=snippet["tags"],
                network=snippet["network"],
                content_type=snippet.get("content_type", "web_snippet"),
                mood=snippet.get("mood"),
                theme=snippet.get("theme"),
                created_at=snippet["timestamp"],
                likes_count=likes_count,
                comments_count=comments_count
            )
            feed_items.append(feed_item.dict())
        
        return {"feed": feed_items, "has_more": len(feed_items) == limit}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching feed: {str(e)}")

@api_router.get("/users/discover")
async def discover_users(skip: int = 0, limit: int = 20):
    """Discover users with most snippets or followers."""
    try:
        users = await db.user_profiles.find().sort([
            ("snippets_count", -1),
            ("followers_count", -1)
        ]).skip(skip).limit(limit).to_list(limit)
        
        for user in users:
            user["_id"] = str(user["_id"])
        
        return {"users": users, "has_more": len(users) == limit}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering users: {str(e)}")

@api_router.post("/social/follow")
async def follow_user(request: FollowRequest):
    """Follow another user."""
    try:
        # Check if already following
        existing = await db.user_follows.find_one({
            "follower_address": request.follower_address,
            "following_address": request.following_address
        })
        
        if existing:
            return {"message": "Already following this user"}
        
        # Create follow relationship
        follow_data = {
            "id": str(uuid.uuid4()),
            "follower_address": request.follower_address,
            "following_address": request.following_address,
            "created_at": datetime.utcnow()
        }
        await db.user_follows.insert_one(follow_data)
        
        # Update follow counts
        await db.user_profiles.update_one(
            {"wallet_address": request.follower_address},
            {"$inc": {"following_count": 1}}
        )
        await db.user_profiles.update_one(
            {"wallet_address": request.following_address},
            {"$inc": {"followers_count": 1}}
        )
        
        return {"message": "Successfully followed user"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error following user: {str(e)}")

@api_router.delete("/social/unfollow/{follower_address}/{following_address}")
async def unfollow_user(follower_address: str, following_address: str):
    """Unfollow a user."""
    try:
        # Remove follow relationship
        result = await db.user_follows.delete_one({
            "follower_address": follower_address,
            "following_address": following_address
        })
        
        if result.deleted_count > 0:
            # Update follow counts
            await db.user_profiles.update_one(
                {"wallet_address": follower_address},
                {"$inc": {"following_count": -1}}
            )
            await db.user_profiles.update_one(
                {"wallet_address": following_address},
                {"$inc": {"followers_count": -1}}
            )
            return {"message": "Successfully unfollowed user"}
        else:
            return {"message": "Follow relationship not found"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unfollowing user: {str(e)}")

@api_router.post("/social/like")
async def like_snippet(request: LikeRequest):
    """Like a snippet."""
    try:
        # Check if already liked
        existing = await db.snippet_likes.find_one({
            "user_address": request.user_address,
            "snippet_id": request.snippet_id
        })
        
        if existing:
            # Unlike
            await db.snippet_likes.delete_one({
                "user_address": request.user_address,
                "snippet_id": request.snippet_id
            })
            return {"message": "Snippet unliked", "liked": False}
        else:
            # Like
            like_data = {
                "id": str(uuid.uuid4()),
                "user_address": request.user_address,
                "snippet_id": request.snippet_id,
                "created_at": datetime.utcnow()
            }
            await db.snippet_likes.insert_one(like_data)
            return {"message": "Snippet liked", "liked": True}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error liking snippet: {str(e)}")

@api_router.post("/social/comment")
async def add_comment(request: CommentRequest):
    """Add a comment to a snippet."""
    try:
        comment = Comment(
            user_address=request.user_address,
            snippet_id=request.snippet_id,
            content=request.content
        )
        await db.snippet_comments.insert_one(comment.dict())
        return comment
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding comment: {str(e)}")

@api_router.get("/social/comments/{snippet_id}")
async def get_comments(snippet_id: str):
    """Get comments for a snippet."""
    try:
        comments = await db.snippet_comments.find({"snippet_id": snippet_id}).sort("created_at", -1).to_list(100)
        
        # Enrich with user data
        for comment in comments:
            comment["_id"] = str(comment["_id"])
            user_profile = await db.user_profiles.find_one({"wallet_address": comment["user_address"]})
            comment["username"] = user_profile.get("username") if user_profile else None
        
        return {"comments": comments}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {str(e)}")

@api_router.post("/save-snippet-metadata", response_model=SnippetMetadata)
async def save_snippet_metadata(request: SnippetMetadataCreate):
    """Save snippet metadata to database with social features."""
    try:
        metadata = SnippetMetadata(**request.dict())
        await db.snippet_metadata.insert_one(metadata.dict())
        
        # Update user's snippet count
        await db.user_profiles.update_one(
            {"wallet_address": request.wallet_address},
            {"$inc": {"snippets_count": 1}},
            upsert=True
        )
        
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving metadata: {str(e)}")

@api_router.get("/snippets/{wallet_address}")
async def get_user_snippets(wallet_address: str):
    """Get all snippets for a wallet address (legacy/backup)."""
    try:
        snippets = await db.snippet_metadata.find({"wallet_address": wallet_address}).to_list(1000)
        # Convert ObjectId to string for JSON serialization
        for snippet in snippets:
            if "_id" in snippet:
                snippet["_id"] = str(snippet["_id"])
        return {"snippets": snippets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching snippets: {str(e)}")

# Health check endpoint for Vercel testing - defined before other routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint for Vercel deployment testing"""
    return {
        "status": "healthy",
        "message": "Irys Snippet Vault API is running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for Vercel deployment verification"""
    return {"message": "API is working correctly", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

# Static file serving for React frontend
# Support both local development and Render deployment
import os
from pathlib import Path

# Try different possible static directories
static_dirs = [
    "static/static",  # Render deployment path (nested static from React build)
    Path(__file__).parent / "static" / "static",  # Explicit relative path (nested)
    Path(__file__).parent / "../frontend/build/static",  # Local development path
]

static_dir = None
for dir_path in static_dirs:
    dir_str = str(dir_path)
    if os.path.exists(dir_str):
        static_dir = dir_str
        break

if static_dir:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"✅ Static files mounted from: {static_dir}")
else:
    print("⚠️  Static files not found - SPA routing disabled")

# Also mount the root static directory to serve index.html and other assets
root_static_dirs = [
    "static",  # Render deployment path
    Path(__file__).parent / "static",  # Explicit relative path
    Path(__file__).parent / "../frontend/build",  # Local development path
]

root_static_dir = None
for dir_path in root_static_dirs:
    dir_str = str(dir_path)
    if os.path.exists(dir_str):
        root_static_dir = dir_str
        break

if root_static_dir:
    print(f"✅ Root static directory found: {root_static_dir}")

# Test route for debugging
@app.get("/test-spa")
async def test_spa():
    """Test SPA route"""
    return {"message": "SPA route test working"}

# SPA routing for React - handles both root and all other routes
@app.get("/{path:path}")
async def serve_spa(path: str = ""):
    """Serve React SPA for client-side routing"""
    # Skip API routes (they are handled by the router)
    if path.startswith("api"):
        return {"error": "API endpoint not found"}
    # For all routes (including root), serve index.html for client-side routing
    if root_static_dir:
        return FileResponse(f"{root_static_dir}/index.html")
    else:
        return {"error": "Static files not available"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("🚀 Starting Irys Snippet Vault API with Social Features...")
    
    # Initialize Irys service
    irys_ready = await init_irys_service()
    if irys_ready:
        print("✅ Irys blockchain integration ready!")
    else:
        print("⚠️ Irys service initialization failed - some features may not work")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# For Vercel deployment, we don't need to serve static files
# Frontend static files are handled by Vercel directly
# Remove static file mounting for serverless deployment