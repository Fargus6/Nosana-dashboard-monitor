from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import requests
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey
import base64
import struct
from passlib.context import CryptContext
from jose import JWTError, jwt

# Set Playwright browser path
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Node(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Link node to user
    address: str
    name: Optional[str] = None
    status: str = "unknown"  # online, offline, unknown
    job_status: Optional[str] = None  # running, queue, idle
    notes: Optional[str] = None
    nos_balance: Optional[float] = None
    sol_balance: Optional[float] = None
    total_jobs: Optional[int] = None
    availability_score: Optional[float] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NodeCreate(BaseModel):
    address: str
    name: Optional[str] = None

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    job_status: Optional[str] = None
    notes: Optional[str] = None

class DashboardLink(BaseModel):
    address: str
    url: str


# Password and token functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": token_data.email}, {"_id": 0})
    if user is None:
        raise credentials_exception
    return User(**user)


async def fetch_node_status_from_solana(address: str) -> dict:
    """Fetch node status from Solana blockchain"""
    try:
        # Connect to Solana mainnet
        solana_client = SolanaClient("https://api.mainnet-beta.solana.com")
        
        # Convert address string to Pubkey
        pubkey = Pubkey.from_string(address)
        
        # Get account info from Solana
        response = solana_client.get_account_info(pubkey)
        
        if response.value is None:
            return {
                'status': 'offline',
                'job_status': None,
                'online': False,
                'error': 'Account not found on Solana'
            }
        
        # Account exists on blockchain
        account_info = response.value
        
        # Check if account has lamports (SOL balance)
        has_balance = account_info.lamports > 0
        has_data = account_info.data is not None and len(account_info.data) > 0
        
        # Determine basic status
        if has_balance and has_data:
            status = 'online'
        elif has_balance:
            status = 'online'
        else:
            status = 'offline'
        
        # Check for active jobs from Nosana Jobs program
        job_status = await check_node_jobs(address, solana_client)
        
        return {
            'status': status,
            'job_status': job_status,
            'online': True,
            'lamports': account_info.lamports,
            'has_data': has_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching node status from Solana: {str(e)}")
        return {
            'status': 'unknown',
            'job_status': None,
            'online': False,
            'error': str(e)
        }


async def check_node_jobs(node_address: str, solana_client: SolanaClient) -> str:
    """Check if node has active jobs by scraping Nosana dashboard"""
    try:
        # First, try the Node.js Nosana SDK service as primary method
        try:
            response = requests.get(
                f"http://localhost:3001/check-node/{node_address}",
                timeout=8
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('jobStatus') != 'idle':
                    return data.get('jobStatus', 'idle')
        except Exception as sdk_error:
            logger.debug(f"SDK service unavailable, trying web scraping: {str(sdk_error)}")
        
        # Fallback to web scraping the dashboard
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = f"https://dashboard.nosana.com/host/{node_address}"
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=20000)
                await page.wait_for_timeout(2000)
                
                # Get page text
                text_content = await page.inner_text('body')
                text_lower = text_content.lower()
                
                await browser.close()
                
                # Parse status from page
                # Look for "STATUS" section and "RUNNING DEPLOYMENT" indicator
                if 'status' in text_lower and 'running' in text_lower:
                    # Check if there's an active running deployment
                    if 'running deployment' in text_lower:
                        logger.info(f"Node {node_address[:8]}... has RUNNING deployment")
                        return 'running'
                    elif 'status\nrunning' in text_lower or 'status:\nrunning' in text_lower:
                        logger.info(f"Node {node_address[:8]}... status is RUNNING")
                        return 'running'
                
                # Check for queued status
                if 'queued' in text_lower or 'queue' in text_lower:
                    logger.info(f"Node {node_address[:8]}... has queued jobs")
                    return 'queue'
                
                # If online but no running/queued jobs
                if 'online' in text_lower or 'host api status\nonline' in text_lower:
                    logger.info(f"Node {node_address[:8]}... is online but idle")
                    return 'idle'
                
                # Default to idle
                return 'idle'
                
            except Exception as page_error:
                await browser.close()
                logger.warning(f"Error scraping dashboard for {node_address[:8]}: {str(page_error)}")
                return 'idle'
            
    except Exception as e:
        logger.error(f"Error checking node jobs: {str(e)}")
        return 'idle'


# Authentication endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_create: UserCreate):
    """Register a new user"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_create.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_create.password)
    user = User(email=user_create.email, hashed_password=hashed_password)
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user"""
    user = await db.users.find_one({"email": form_data.username}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.post("/auth/google")
async def google_auth(session_id: str):
    """Process Google OAuth session"""
    try:
        # Call Emergent auth service to get session data
        headers = {"X-Session-ID": session_id}
        response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        data = response.json()
        email = data.get("email")
        name = data.get("name")
        session_token = data.get("session_token")
        
        if not email or not session_token:
            raise HTTPException(status_code=401, detail="Invalid session data")
        
        # Check if user exists, if not create one
        user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if not user:
            # Create new user with Google auth
            new_user = User(
                email=email,
                hashed_password=""  # No password for Google auth users
            )
            user_dict = new_user.model_dump()
            user_dict['created_at'] = user_dict['created_at'].isoformat()
            await db.users.insert_one(user_dict)
            user = user_dict
        
        # Store session token in database with expiry
        expiry = datetime.now(timezone.utc) + timedelta(days=7)
        await db.sessions.update_one(
            {"email": email},
            {
                "$set": {
                    "session_token": session_token,
                    "expiry": expiry.isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        # Create JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "session_token": session_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {"email": current_user.email, "id": current_user.id}


@api_router.post("/nodes", response_model=Node)
async def add_node(input: NodeCreate, current_user: User = Depends(get_current_user)):
    """Add a new node to monitor"""
    # Check if node already exists for this user
    existing = await db.nodes.find_one({"address": input.address, "user_id": current_user.id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Node already exists")
    
    node_dict = input.model_dump()
    node_dict['user_id'] = current_user.id  # Associate with current user
    node_obj = Node(**node_dict)
    
    doc = node_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['last_updated'] = doc['last_updated'].isoformat()
    
    await db.nodes.insert_one(doc)
    return node_obj


@api_router.get("/nodes", response_model=List[Node])
async def get_nodes(current_user: User = Depends(get_current_user)):
    """Get all monitored nodes for current user"""
    nodes = await db.nodes.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    
    for node in nodes:
        if isinstance(node.get('created_at'), str):
            node['created_at'] = datetime.fromisoformat(node['created_at'])
        if isinstance(node.get('last_updated'), str):
            node['last_updated'] = datetime.fromisoformat(node['last_updated'])
    
    return nodes


@api_router.put("/nodes/{node_id}", response_model=Node)
async def update_node(node_id: str, update: NodeUpdate, current_user: User = Depends(get_current_user)):
    """Update node information"""
    node = await db.nodes.find_one({"id": node_id, "user_id": current_user.id}, {"_id": 0})
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    update_data = update.model_dump(exclude_none=True)
    update_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    await db.nodes.update_one(
        {"id": node_id, "user_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_node = await db.nodes.find_one({"id": node_id}, {"_id": 0})
    
    # Convert dates
    if isinstance(updated_node.get('created_at'), str):
        updated_node['created_at'] = datetime.fromisoformat(updated_node['created_at'])
    if isinstance(updated_node.get('last_updated'), str):
        updated_node['last_updated'] = datetime.fromisoformat(updated_node['last_updated'])
    
    return Node(**updated_node)


@api_router.delete("/nodes/{node_id}")
async def delete_node(node_id: str, current_user: User = Depends(get_current_user)):
    """Delete a node"""
    result = await db.nodes.delete_one({"id": node_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node deleted successfully"}


@api_router.get("/nodes/{address}/check-status")
async def check_node_status_blockchain(address: str):
    """Check node status from Solana blockchain"""
    status_data = await fetch_node_status_from_solana(address)
    return status_data


@api_router.post("/nodes/refresh-all-status")
async def refresh_all_nodes_status(current_user: User = Depends(get_current_user)):
    """Automatically refresh status for all nodes from Solana blockchain"""
    nodes = await db.nodes.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    updated_count = 0
    errors = []
    
    for node in nodes:
        try:
            address = node['address']
            previous_status = node.get('status', 'unknown')
            
            # Fetch status from Solana
            status_data = await fetch_node_status_from_solana(address)
            current_status = status_data['status']
            
            # Update node in database
            await db.nodes.update_one(
                {"address": address, "user_id": current_user.id},
                {"$set": {
                    "status": current_status,
                    "job_status": status_data.get('job_status'),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            updated_count += 1
            
        except Exception as e:
            errors.append({"address": node['address'], "error": str(e)})
            logger.error(f"Error updating node {node['address']}: {str(e)}")
    
    return {
        "updated": updated_count,
        "total": len(nodes),
        "errors": errors
    }


@api_router.get("/nodes/{address}/dashboard", response_model=DashboardLink)
async def get_dashboard_link(address: str):
    """Get Nosana dashboard link for a node"""
    return DashboardLink(
        address=address,
        url=f"https://dashboard.nosana.com/host/{address}"
    )


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()