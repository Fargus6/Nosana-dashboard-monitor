from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr, validator
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import requests
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey
import base64
import struct
from passlib.context import CryptContext
from jose import JWTError, jwt
import re
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import html
import secrets
import firebase_admin
from firebase_admin import credentials, messaging
from telegram import Bot
from telegram.constants import ParseMode
import asyncio
from bs4 import BeautifulSoup

# Set Playwright browser path
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Failed login attempts tracking (in-memory for simplicity, use Redis in production)
failed_login_attempts = {}
locked_accounts = {}

# Password strength validator
def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

# Input sanitization
def sanitize_string(text: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return text
    # HTML escape
    sanitized = html.escape(text)
    # Remove any control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    return sanitized

# Validate Solana address format
def validate_solana_address(address: str) -> bool:
    """Validate that address is a valid Solana address format"""
    if not address or not isinstance(address, str):
        return False
    # Solana addresses are base58 encoded and typically 32-44 characters
    if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address):
        return False
    return True

# Check if account is locked
def is_account_locked(email: str) -> bool:
    """Check if account is locked due to failed login attempts"""
    if email in locked_accounts:
        lockout_time = locked_accounts[email]
        if datetime.now(timezone.utc) < lockout_time:
            return True
        else:
            # Lockout period expired, remove from locked accounts
            del locked_accounts[email]
            if email in failed_login_attempts:
                del failed_login_attempts[email]
    return False

# Record failed login attempt
def record_failed_login(email: str):
    """Record a failed login attempt and lock account if threshold exceeded"""
    if email not in failed_login_attempts:
        failed_login_attempts[email] = []
    
    # Add current timestamp
    failed_login_attempts[email].append(datetime.now(timezone.utc))
    
    # Remove attempts older than lockout period
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
    failed_login_attempts[email] = [
        attempt for attempt in failed_login_attempts[email] 
        if attempt > cutoff_time
    ]
    
    # Lock account if too many attempts
    if len(failed_login_attempts[email]) >= MAX_LOGIN_ATTEMPTS:
        locked_accounts[email] = datetime.now(timezone.utc) + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        logger.warning(f"Account locked for {email} due to excessive failed login attempts")

# Clear failed login attempts on successful login
def clear_failed_login(email: str):
    """Clear failed login attempts for successful login"""
    if email in failed_login_attempts:
        del failed_login_attempts[email]
    if email in locked_accounts:
        del locked_accounts[email]

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configure logging EARLY
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin
try:
    cred = credentials.Certificate("/app/backend/firebase-credentials.json")
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {str(e)}")

# Initialize Telegram Bot
telegram_bot = None
try:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if TELEGRAM_TOKEN:
        telegram_bot = Bot(token=TELEGRAM_TOKEN)
        logger.info("Telegram Bot initialized successfully")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not found in environment")
except Exception as e:
    logger.error(f"Failed to initialize Telegram Bot: {str(e)}")

# Create the main app without a prefix
app = FastAPI()

# Custom rate limit exception handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceptions with helpful messages"""
    path = request.url.path
    
    # Check if it's the registration endpoint
    if "/auth/register" in path:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Registration limit reached. Please wait until the next hour to create a new account. We allow 30 registrations per hour to prevent abuse."
            }
        )
    
    # Default message for other endpoints
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."}
    )

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Security Middleware for headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://demobackend.emergentagent.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.mainnet-beta.solana.com https://dashboard.nosana.com https://accounts.google.com https://demobackend.emergentagent.com; "
            "frame-src 'self' https://accounts.google.com;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log incoming request
        logger.info(f"Request: {request.method} {request.url.path} from {request.client.host}")
        
        # Process request
        response = await call_next(request)
        
        # Log response status
        logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
        
        return response

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

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
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one number')
        return v

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
    gpu_type: Optional[str] = "3090"  # GPU type for earnings calculation (3090, A100, Pro6000, H100)
    status: str = "unknown"  # online, offline, unknown
    job_status: Optional[str] = None  # running, queue, idle
    notes: Optional[str] = None
    nos_balance: Optional[float] = None
    sol_balance: Optional[float] = None
    total_jobs: Optional[int] = None
    availability_score: Optional[float] = None
    job_start_time: Optional[str] = None  # ISO timestamp when job started
    job_count_completed: Optional[int] = 0  # Track completed jobs count
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NodeCreate(BaseModel):
    address: str
    name: Optional[str] = None
    
    @validator('address')
    def validate_address(cls, v):
        if not validate_solana_address(v):
            raise ValueError('Invalid Solana address format')
        return v
    
    @validator('name')
    def sanitize_name(cls, v):
        if v:
            return sanitize_string(v)
        return v

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    job_status: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('name', 'notes')
    def sanitize_text(cls, v):
        if v:
            return sanitize_string(v)
        return v

# Notification Models
class DeviceToken(BaseModel):
    token: str
    user_id: str
    device_info: Optional[Dict] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class NotificationPreferences(BaseModel):
    user_id: str
    notify_offline: bool = True
    notify_online: bool = True
    notify_job_started: bool = True
    notify_job_completed: bool = True
    vibration: bool = True
    sound: bool = True
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
                'nos_balance': None,
                'sol_balance': None,
                'total_jobs': None,
                'availability_score': None,
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
        
        # Get SOL balance
        sol_balance = account_info.lamports / 1e9  # Convert lamports to SOL
        
        # Check for active jobs from Nosana Jobs program
        job_data = await check_node_jobs(address, solana_client)
        
        return {
            'status': status,
            'job_status': job_data.get('job_status'),
            'online': True,
            'lamports': account_info.lamports,
            'has_data': has_data,
            'sol_balance': sol_balance,
            'nos_balance': job_data.get('nos_balance'),
            'total_jobs': job_data.get('total_jobs'),
            'availability_score': job_data.get('availability_score')
        }
        
    except Exception as e:
        logger.error(f"Error fetching node status from Solana: {str(e)}")
        return {
            'status': 'unknown',
            'job_status': None,
            'online': False,
            'sol_balance': None,
            'nos_balance': None,
            'total_jobs': None,
            'availability_score': None,
            'error': str(e)
        }


async def check_node_jobs(node_address: str, solana_client: SolanaClient) -> dict:
    """
    Check node jobs using multiple methods (Playwright scraping)
    Returns job status, NOS balance, SOL balance, and other stats
    """
    try:
        # First, try to get NOS balance directly from Solana blockchain
        nos_balance = None
        try:
            from solders.pubkey import Pubkey as SoldersPubkey
            from solana.rpc.types import TokenAccountOpts
            
            # NOS token mint address
            NOS_MINT = "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7"
            
            wallet_pubkey = SoldersPubkey.from_string(node_address)
            nos_mint_pubkey = SoldersPubkey.from_string(NOS_MINT)
            
            # Get all NOS token accounts for this wallet
            opts = TokenAccountOpts(mint=nos_mint_pubkey)
            response = solana_client.get_token_accounts_by_owner(wallet_pubkey, opts)
            
            if response and response.value:
                # Sum up balances from all token accounts
                total_nos_balance = 0.0
                for account in response.value:
                    token_account_pubkey = SoldersPubkey.from_string(str(account.pubkey))
                    balance_response = solana_client.get_token_account_balance(token_account_pubkey)
                    if balance_response and balance_response.value:
                        # Use ui_amount for human-readable balance with decimals
                        account_balance = balance_response.value.ui_amount
                        if account_balance:
                            total_nos_balance += account_balance
                
                if total_nos_balance > 0:
                    nos_balance = total_nos_balance
                    logger.info(f"✅ Got NOS balance from blockchain: {nos_balance:.2f} NOS for {node_address[:8]}...")
        except Exception as nos_error:
            logger.debug(f"Could not get NOS balance from blockchain: {str(nos_error)}")
        
        # First, try the Node.js Nosana SDK service as primary method for job status
        try:
            response = requests.get(
                f"http://localhost:3001/check-node/{node_address}",
                timeout=8
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('jobStatus') != 'idle':
                    return {
                        'job_status': data.get('jobStatus', 'idle'),
                        'nos_balance': nos_balance,  # Use blockchain balance
                        'sol_balance': None,
                        'total_jobs': None,
                        'availability_score': None
                    }
        except Exception as sdk_error:
            logger.debug(f"SDK service unavailable, trying web scraping: {str(sdk_error)}")
        
        # Fallback to web scraping the dashboard
        from playwright.async_api import async_playwright
        import re
        
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
                
                # Parse job status
                job_status = 'idle'
                if 'status' in text_lower and 'running' in text_lower:
                    if 'running deployment' in text_lower:
                        logger.info(f"Node {node_address[:8]}... has RUNNING deployment")
                        job_status = 'running'
                    elif 'status\nrunning' in text_lower or 'status:\nrunning' in text_lower:
                        logger.info(f"Node {node_address[:8]}... status is RUNNING")
                        job_status = 'running'
                
                if 'queued' in text_lower or 'queue' in text_lower:
                    logger.info(f"Node {node_address[:8]}... has queued jobs")
                    job_status = 'queue'
                
                if 'online' in text_lower or 'host api status\nonline' in text_lower:
                    logger.info(f"Node {node_address[:8]}... is online but idle")
                
                # Extract NOS balance from scraping (if not already got from blockchain)
                scraped_nos_balance = None
                nos_match = re.search(r'(\d+\.?\d*)\s*nos', text_lower)
                if nos_match:
                    scraped_nos_balance = float(nos_match.group(1))
                
                # Use blockchain balance if available, otherwise use scraped balance
                final_nos_balance = nos_balance if nos_balance is not None else scraped_nos_balance
                
                # Extract SOL balance
                sol_balance = None
                sol_match = re.search(r'(\d+\.?\d*)\s*sol', text_lower)
                if sol_match:
                    sol_balance = float(sol_match.group(1))
                
                # Extract total jobs
                total_jobs = None
                jobs_match = re.search(r'(\d+)\s*job', text_lower)
                if jobs_match:
                    total_jobs = int(jobs_match.group(1))
                
                # Extract availability score (percentage)
                availability_score = None
                avail_match = re.search(r'availability[:\s]+(\d+\.?\d*)%', text_lower)
                if not avail_match:
                    avail_match = re.search(r'uptime[:\s]+(\d+\.?\d*)%', text_lower)
                if avail_match:
                    availability_score = float(avail_match.group(1))
                
                return {
                    'job_status': job_status,
                    'nos_balance': final_nos_balance,
                    'sol_balance': sol_balance,
                    'total_jobs': total_jobs,
                    'availability_score': availability_score
                }
                
            except Exception as page_error:
                await browser.close()
                logger.warning(f"Error scraping dashboard for {node_address[:8]}: {str(page_error)}")
                return {
                    'job_status': 'idle',
                    'nos_balance': nos_balance,  # Still return blockchain balance even if scraping fails
                    'sol_balance': None,
                    'total_jobs': None,
                    'availability_score': None
                }
            
    except Exception as e:
        logger.error(f"Error checking node jobs: {str(e)}")
        return {
            'job_status': 'idle',
            'nos_balance': nos_balance if 'nos_balance' in locals() else None,  # Return blockchain balance if available
            'sol_balance': None,
            'total_jobs': None,
            'availability_score': None
        }


# Authentication endpoints
@api_router.post("/auth/register", response_model=Token)
@limiter.limit("30/hour")  # Allow 30 registrations per hour per IP
async def register(request: Request, user_create: UserCreate):
    """Register a new user"""
    # Sanitize email (already validated by EmailStr)
    email = user_create.email.lower().strip()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_create.password)
    user = User(email=email, hashed_password=hashed_password)
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    logger.info(f"New user registered: {email}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")  # Rate limit login attempts
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user"""
    email = form_data.username.lower().strip()
    
    # Check if account is locked
    if is_account_locked(email):
        remaining_time = locked_accounts.get(email)
        if remaining_time:
            minutes_left = int((remaining_time - datetime.now(timezone.utc)).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked due to multiple failed login attempts. Try again in {minutes_left} minutes.",
            )
    
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        record_failed_login(email)
        logger.warning(f"Failed login attempt for non-existent user: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user['hashed_password']):
        record_failed_login(email)
        logger.warning(f"Failed login attempt for user: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Clear failed attempts on successful login
    clear_failed_login(email)
    logger.info(f"Successful login: {email}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.post("/auth/google")
@limiter.limit("10/minute")
async def google_auth(request: Request, session_id: str):
    """Process Google OAuth session"""
    try:
        # Validate session_id format
        if not session_id or len(session_id) < 10:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        # Call Emergent auth service to get session data
        headers = {"X-Session-ID": session_id}
        response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.warning(f"Google auth failed: Invalid session {session_id[:10]}...")
            raise HTTPException(status_code=401, detail="Invalid session")
        
        data = response.json()
        email = data.get("email")
        # name = data.get("name")  # Not used currently
        session_token = data.get("session_token")
        
        if not email or not session_token:
            raise HTTPException(status_code=401, detail="Invalid session data")
        
        # Sanitize and normalize email
        email = email.lower().strip()
        
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
            logger.info(f"New Google user registered: {email}")
        else:
            logger.info(f"Google login: {email}")
        
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


# Notification endpoints
@api_router.post("/notifications/register-token")
@limiter.limit("10/hour")
async def register_device_token(request: Request, token: str, current_user: User = Depends(get_current_user)):
    """Register FCM device token for push notifications"""
    try:
        logger.info(f"=" * 70)
        logger.info(f"📱 REGISTERING DEVICE TOKEN")
        logger.info(f"   User: {current_user.email}")
        logger.info(f"   User ID: {current_user.id}")
        logger.info(f"   Token preview: {token[:30]}...{token[-10:]}")
        
        device_token = DeviceToken(
            token=token,
            user_id=current_user.id
        )
        
        # Check if token already exists
        existing = await db.device_tokens.find_one({"token": token})
        if existing:
            logger.info(f"   ♻️  Token already exists, updating...")
            # Update existing
            await db.device_tokens.update_one(
                {"token": token},
                {"$set": {"user_id": current_user.id, "created_at": datetime.now(timezone.utc).isoformat()}}
            )
            logger.info(f"   ✅ Token updated successfully")
        else:
            logger.info(f"   ➕ Registering new token...")
            # Insert new
            token_dict = device_token.model_dump()
            await db.device_tokens.insert_one(token_dict)
            logger.info(f"   ✅ New token registered successfully")
        
        # Count total tokens for this user
        user_tokens_count = await db.device_tokens.count_documents({"user_id": current_user.id})
        logger.info(f"   📊 User now has {user_tokens_count} device(s) registered")
        logger.info(f"=" * 70)
        
        return {"status": "success", "message": "Device token registered", "total_devices": user_tokens_count}
    except Exception as e:
        logger.error(f"=" * 70)
        logger.error(f"❌ ERROR REGISTERING DEVICE TOKEN")
        logger.error(f"   User: {current_user.email if current_user else 'Unknown'}")
        logger.error(f"   Error: {str(e)}")
        logger.error(f"=" * 70)
        raise HTTPException(status_code=500, detail="Failed to register device token")


@api_router.get("/notifications/preferences")
async def get_notification_preferences(current_user: User = Depends(get_current_user)):
    """Get user notification preferences"""
    prefs = await db.notification_preferences.find_one({"user_id": current_user.id}, {"_id": 0})
    if not prefs:
        # Return default preferences
        return {
            "user_id": current_user.id,
            "notify_offline": True,
            "notify_online": True,
            "notify_job_started": True,
            "notify_job_completed": True,
            "vibration": True,
            "sound": True
        }
    return prefs


@api_router.post("/notifications/preferences")
@limiter.limit("20/hour")
async def save_notification_preferences(
    request: Request,
    preferences: NotificationPreferences,
    current_user: User = Depends(get_current_user)
):
    """Save user notification preferences"""
    preferences.user_id = current_user.id
    prefs_dict = preferences.model_dump()
    
    await db.notification_preferences.update_one(
        {"user_id": current_user.id},
        {"$set": prefs_dict},
        upsert=True
    )
    
    logger.info(f"Notification preferences updated for user {current_user.email}")
    return {"status": "success", "message": "Preferences saved"}


@api_router.post("/notifications/test")
@limiter.limit("5/hour")
async def send_test_notification(request: Request, current_user: User = Depends(get_current_user)):
    """Send a test notification to user's devices"""
    try:
        # Get user's device tokens
        tokens = await db.device_tokens.find({"user_id": current_user.id}).to_list(100)
        
        if not tokens:
            raise HTTPException(status_code=404, detail="No devices registered for push notifications")
        
        # Send test notification to all devices
        sent_count = 0
        for device in tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="🔔 Test Notification",
                        body="Your Nosana Node Monitor notifications are working!",
                    ),
                    token=device['token']
                )
                
                response = messaging.send(message)
                sent_count += 1
                logger.info(f"Test notification sent: {response}")
            except Exception as e:
                logger.error(f"Failed to send to token: {str(e)}")
                # Remove invalid tokens
                if "invalid" in str(e).lower() or "not registered" in str(e).lower():
                    await db.device_tokens.delete_one({"token": device['token']})
        
        return {"status": "success", "sent": sent_count, "total": len(tokens)}
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/notifications/telegram/link")
@limiter.limit("10/hour")
async def link_telegram_account(request: Request, link_code: str, current_user: User = Depends(get_current_user)):
    """Link Telegram account using code from /start command"""
    try:
        # Find the link code
        link_data = await db.telegram_link_codes.find_one({"link_code": link_code.upper()})
        
        if not link_data:
            raise HTTPException(status_code=404, detail="Invalid link code. Use /start in Telegram bot to get a new code.")
        
        chat_id = link_data['chat_id']
        
        # Check if already linked
        existing = await db.telegram_users.find_one({"user_id": current_user.id})
        if existing:
            # Update existing
            await db.telegram_users.update_one(
                {"user_id": current_user.id},
                {"$set": {"chat_id": chat_id, "linked_at": datetime.now(timezone.utc).isoformat()}}
            )
        else:
            # Create new link
            await db.telegram_users.insert_one({
                "user_id": current_user.id,
                "chat_id": chat_id,
                "username": link_data.get('username'),
                "linked_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Delete used link code
        await db.telegram_link_codes.delete_one({"link_code": link_code.upper()})
        
        # Send confirmation to Telegram
        if telegram_bot:
            try:
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ **Account Linked Successfully!**\n\nYou'll now receive notifications for:\n• Node offline alerts\n• Low SOL balance warnings\n• Node online confirmations\n\nUse /status to check your nodes anytime!",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
        
        return {"status": "success", "message": "Telegram account linked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking Telegram account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/notifications/telegram/status")
@limiter.limit("30/minute")
async def get_telegram_link_status(request: Request, current_user: User = Depends(get_current_user)):
    """Check if user has linked Telegram account"""
    try:
        telegram_user = await db.telegram_users.find_one({"user_id": current_user.id})
        
        if telegram_user:
            return {
                "linked": True,
                "username": telegram_user.get('username'),
                "linked_at": telegram_user.get('linked_at')
            }
        else:
            return {"linked": False}
    except Exception as e:
        logger.error(f"Error checking Telegram status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/notifications/telegram/unlink")
@limiter.limit("10/hour")
async def unlink_telegram_account(request: Request, current_user: User = Depends(get_current_user)):
    """Unlink Telegram account"""
    try:
        result = await db.telegram_users.delete_one({"user_id": current_user.id})
        
        if result.deleted_count > 0:
            return {"status": "success", "message": "Telegram account unlinked"}
        else:
            raise HTTPException(status_code=404, detail="No linked Telegram account found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking Telegram account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_telegram_notification(user_id: str, message: str):
    """Send notification via Telegram"""
    if not telegram_bot:
        return
    
    try:
        # Find user's Telegram chat_id
        telegram_user = await db.telegram_users.find_one({"user_id": user_id})
        
        if not telegram_user:
            logger.debug(f"No Telegram linked for user {user_id}")
            return
        
        chat_id = telegram_user['chat_id']
        
        # Send message
        await telegram_bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"✅ Telegram notification sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {str(e)}")



async def get_nos_token_price() -> Optional[float]:
    """Fetch current NOS token price in USD from CoinGecko API"""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=nosana&vs_currencies=usd",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            price = data.get('nosana', {}).get('usd')
            if price:
                logger.info(f"💰 NOS Token Price: ${price:.4f} USD")
                return float(price)
        logger.warning(f"Failed to fetch NOS price: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching NOS price: {str(e)}")
    return None


async def scrape_nosana_job_history(node_address: str) -> List[Dict]:
    """
    Scrape actual job history data from Nosana dashboard using Playwright
    
    Returns list of jobs with real payment data:
    [
        {
            "job_id": "...",
            "started": str,
            "duration_seconds": int,
            "hourly_rate_usd": float,  # Actual rate from dashboard
            "gpu_type": str,
            "status": str
        }
    ]
    """
    try:
        from playwright.async_api import async_playwright
        
        url = f"https://dashboard.nosana.com/host/{node_address}"
        logger.info(f"🌐 Scraping Nosana dashboard for node: {node_address}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                # Navigate to page
                await page.goto(url, wait_until='networkidle', timeout=15000)
                
                # Wait for table to load
                await page.wait_for_selector('table', timeout=10000)
                
                # Extract job data from table using JavaScript
                jobs_data = await page.evaluate('''() => {
                    const jobs = [];
                    const table = document.querySelector('table');
                    if (!table) return jobs;
                    
                    const rows = table.querySelectorAll('tr');
                    
                    for (let i = 1; i < rows.length; i++) {
                        const row = rows[i];
                        const cells = row.querySelectorAll('td');
                        
                        if (cells.length >= 6) {
                            const jobLink = cells[0].querySelector('a');
                            const jobId = jobLink ? jobLink.getAttribute('href').split('/').pop() : null;
                            
                            jobs.push({
                                job_id: jobId,
                                started: cells[2].textContent.trim(),
                                duration: cells[3].textContent.trim(),
                                price: cells[4].textContent.trim(),
                                gpu: cells[5].textContent.trim(),
                                status: cells[6].textContent.trim().includes('RUNNING') ? 'RUNNING' : 'SUCCESS'
                            });
                        }
                    }
                    
                    return jobs;
                }''')
                
                await browser.close()
                
                # Parse the extracted data
                jobs = []
                for job_data in jobs_data:
                    duration_seconds = parse_duration_to_seconds(job_data['duration'])
                    hourly_rate = parse_hourly_rate(job_data['price'])
                    started_time = parse_relative_time(job_data['started'])
                    
                    job = {
                        "job_id": job_data['job_id'],
                        "started": started_time,
                        "started_text": job_data['started'],
                        "duration_seconds": duration_seconds,
                        "duration_text": job_data['duration'],
                        "hourly_rate_usd": hourly_rate,
                        "gpu_type": job_data['gpu'],
                        "status": job_data['status']
                    }
                    
                    jobs.append(job)
                    logger.info(f"📊 Job {job_data['job_id'][:8] if job_data['job_id'] else 'N/A'}...: {job_data['duration']} @ ${hourly_rate}/h = ${(duration_seconds/3600.0)*hourly_rate:.4f}")
                
                logger.info(f"✅ Scraped {len(jobs)} jobs from Nosana dashboard")
                return jobs
                
            except Exception as e:
                await browser.close()
                logger.error(f"Error during Playwright scraping: {str(e)}")
                return []
        
    except Exception as e:
        logger.error(f"Error scraping Nosana dashboard: {str(e)}")
        return []


def parse_duration_to_seconds(duration_text: str) -> int:
    """Convert duration text like '55m 9s' or '1h 23m' to seconds"""
    try:
        seconds = 0
        # Match hours
        hours_match = re.search(r'(\d+)h', duration_text)
        if hours_match:
            seconds += int(hours_match.group(1)) * 3600
        
        # Match minutes
        minutes_match = re.search(r'(\d+)m', duration_text)
        if minutes_match:
            seconds += int(minutes_match.group(1)) * 60
        
        # Match seconds
        seconds_match = re.search(r'(\d+)s', duration_text)
        if seconds_match:
            seconds += int(seconds_match.group(1))
        
        return seconds
    except Exception as e:
        logger.error(f"Error parsing duration '{duration_text}': {str(e)}")
        return 0


def parse_hourly_rate(price_text: str) -> float:
    """Extract hourly rate from price text like '$0.176' or '$0.192/h'"""
    try:
        # Remove '/h' suffix and '$' prefix
        rate_str = price_text.replace('/h', '').replace('$', '').strip()
        return float(rate_str)
    except Exception as e:
        logger.error(f"Error parsing hourly rate '{price_text}': {str(e)}")
        return 0.0


def parse_relative_time(time_text: str) -> datetime:
    """Convert relative time like '3 hours ago' to datetime"""
    try:
        now = datetime.now(timezone.utc)
        
        # Match patterns like "3 hours ago", "33 minutes ago", "2 days ago"
        hours_match = re.search(r'(\d+)\s+hours?\s+ago', time_text)
        if hours_match:
            return now - timedelta(hours=int(hours_match.group(1)))
        
        minutes_match = re.search(r'(\d+)\s+minutes?\s+ago', time_text)
        if minutes_match:
            return now - timedelta(minutes=int(minutes_match.group(1)))
        
        days_match = re.search(r'(\d+)\s+days?\s+ago', time_text)
        if days_match:
            return now - timedelta(days=int(days_match.group(1)))
        
        # Default to now if can't parse
        return now
    except Exception as e:
        logger.error(f"Error parsing relative time '{time_text}': {str(e)}")
        return datetime.now(timezone.utc)


async def store_scraped_jobs(user_id: str, node_address: str, jobs: List[Dict]):
    """
    Store scraped jobs from Nosana dashboard in MongoDB
    Prevents duplicates by job_id
    """
    try:
        if not jobs:
            return 0
        
        nos_price = fetch_nos_price_coingecko() or 0.1
        stored_count = 0
        
        for job in jobs:
            # Skip if job already exists
            existing = await db.scraped_jobs.find_one({
                "job_id": job['job_id'],
                "node_address": node_address
            })
            
            if existing:
                continue
            
            # Calculate earnings
            duration_hours = job['duration_seconds'] / 3600.0
            usd_earned = duration_hours * job['hourly_rate_usd']
            nos_earned = usd_earned / nos_price if nos_price > 0 else 0
            
            # Store job
            job_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "node_address": node_address,
                "job_id": job['job_id'],
                "started": job['started'].isoformat() if isinstance(job['started'], datetime) else job['started'],
                "started_text": job.get('started_text', ''),
                "completed": job['started'].isoformat() if job['status'] == 'SUCCESS' else None,
                "duration_seconds": job['duration_seconds'],
                "duration_text": job.get('duration_text', ''),
                "hourly_rate_usd": job['hourly_rate_usd'],
                "usd_earned": round(usd_earned, 4),
                "nos_earned": round(nos_earned, 2),
                "nos_price_at_time": nos_price,
                "gpu_type": job['gpu_type'],
                "status": job['status'],
                "scraped_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.scraped_jobs.insert_one(job_doc)
            stored_count += 1
        
        logger.info(f"✅ Stored {stored_count} new jobs for node {node_address[:8]}...")
        return stored_count
        
    except Exception as e:
        logger.error(f"Error storing scraped jobs: {str(e)}")
        return 0


async def get_yesterday_scraped_earnings(user_id: str, node_address: str) -> Dict:
    """Get yesterday's earnings from scraped data"""
    try:
        yesterday_start = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday_start + timedelta(days=1)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "node_address": node_address,
                    "status": "SUCCESS",
                    "completed": {
                        "$gte": yesterday_start.isoformat(),
                        "$lt": yesterday_end.isoformat()
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_usd": {"$sum": "$usd_earned"},
                    "total_nos": {"$sum": "$nos_earned"},
                    "total_jobs": {"$sum": 1},
                    "total_duration": {"$sum": "$duration_seconds"}
                }
            }
        ]
        
        result = await db.scraped_jobs.aggregate(pipeline).to_list(1)
        
        if result:
            return {
                "date": yesterday_start.strftime("%Y-%m-%d"),
                "usd_earned": round(result[0]['total_usd'], 2),
                "nos_earned": round(result[0]['total_nos'], 2),
                "job_count": result[0]['total_jobs'],
                "duration_seconds": result[0]['total_duration']
            }
        
        return {
            "date": yesterday_start.strftime("%Y-%m-%d"),
            "usd_earned": 0,
            "nos_earned": 0,
            "job_count": 0,
            "duration_seconds": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting yesterday scraped earnings: {str(e)}")
        return {"date": "", "usd_earned": 0, "nos_earned": 0, "job_count": 0, "duration_seconds": 0}


async def get_monthly_scraped_earnings(user_id: str, node_address: str) -> Dict:
    """Get monthly breakdown from scraped data"""
    try:
        # Get all completed jobs
        jobs = await db.scraped_jobs.find({
            "user_id": user_id,
            "node_address": node_address,
            "status": "SUCCESS",
            "completed": {"$ne": None}
        }).to_list(None)
        
        if not jobs:
            return {"months": []}
        
        # Group by month
        monthly_data = {}
        for job in jobs:
            completed_date = datetime.fromisoformat(job['completed'].replace('Z', '+00:00'))
            month_key = completed_date.strftime("%Y-%m")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_key,
                    "usd_earned": 0,
                    "nos_earned": 0,
                    "job_count": 0,
                    "duration_seconds": 0
                }
            
            monthly_data[month_key]["usd_earned"] += job.get('usd_earned', 0)
            monthly_data[month_key]["nos_earned"] += job.get('nos_earned', 0)
            monthly_data[month_key]["job_count"] += 1
            monthly_data[month_key]["duration_seconds"] += job.get('duration_seconds', 0)
        
        # Convert to sorted list
        months = []
        for month_key in sorted(monthly_data.keys(), reverse=True):
            data = monthly_data[month_key]
            year, month = month_key.split('-')
            month_name = datetime(int(year), int(month), 1).strftime("%B %Y")
            
            months.append({
                "month": month_key,
                "month_name": month_name,
                "usd_earned": round(data["usd_earned"], 2),
                "nos_earned": round(data["nos_earned"], 2),
                "job_count": data["job_count"],
                "duration_seconds": data["duration_seconds"]
            })
        
        return {"months": months[:12]}  # Last 12 months
        
    except Exception as e:
        logger.error(f"Error getting monthly scraped earnings: {str(e)}")
        return {"months": []}


async def get_yearly_scraped_earnings(user_id: str, node_address: str) -> Dict:
    """Get yearly totals from scraped data"""
    try:
        # Get all completed jobs
        jobs = await db.scraped_jobs.find({
            "user_id": user_id,
            "node_address": node_address,
            "status": "SUCCESS",
            "completed": {"$ne": None}
        }).to_list(None)
        
        if not jobs:
            return {"years": []}
        
        # Group by year
        yearly_data = {}
        for job in jobs:
            completed_date = datetime.fromisoformat(job['completed'].replace('Z', '+00:00'))
            year_key = completed_date.strftime("%Y")
            
            if year_key not in yearly_data:
                yearly_data[year_key] = {
                    "year": year_key,
                    "usd_earned": 0,
                    "nos_earned": 0,
                    "job_count": 0,
                    "duration_seconds": 0
                }
            
            yearly_data[year_key]["usd_earned"] += job.get('usd_earned', 0)
            yearly_data[year_key]["nos_earned"] += job.get('nos_earned', 0)
            yearly_data[year_key]["job_count"] += 1
            yearly_data[year_key]["duration_seconds"] += job.get('duration_seconds', 0)
        
        # Convert to sorted list
        years = []
        for year_key in sorted(yearly_data.keys(), reverse=True):
            data = yearly_data[year_key]
            years.append({
                "year": year_key,
                "usd_earned": round(data["usd_earned"], 2),
                "nos_earned": round(data["nos_earned"], 2),
                "job_count": data["job_count"],
                "duration_seconds": data["duration_seconds"]
            })
        
        return {"years": years}
        
    except Exception as e:
        logger.error(f"Error getting yearly scraped earnings: {str(e)}")
        return {"years": []}


def calculate_job_payment(duration_seconds: int, nos_price_usd: Optional[float], gpu_type: str = "A100") -> Optional[float]:
    """
    Calculate NOS payment for a job based on Nosana's payment structure
    
    Payment Formula: (hourly_rate × duration_hours) / nos_price
    
    GPU Hourly Rates (from Nosana):
    - RTX 3090: $0.176/hr
    - A100 80GB: $0.294/hr (estimated from dashboard)
    - RTX Pro 6000: $0.30/hr
    - H100: $0.40/hr
    
    Args:
        duration_seconds: Job duration in seconds
        nos_price_usd: Current NOS token price in USD
        gpu_type: Type of GPU (defaults to A100)
    
    Returns:
        Payment in NOS tokens, or None if calculation fails
    """
    try:
        # Real Nosana GPU hourly rates
        gpu_hourly_rates = {
            "3090": 0.176,      # RTX 3090
            "RTX3090": 0.176,
            "A100": 0.294,      # A100 80GB (from dashboard avg)
            "Pro6000": 0.30,    # RTX Pro 6000
            "H100": 0.40,       # H100
            "default": 0.176    # Default to 3090 rate
        }
        
        hourly_rate = gpu_hourly_rates.get(gpu_type, gpu_hourly_rates["default"])
        
        # Calculate USD based on duration
        duration_hours = duration_seconds / 3600.0
        usd_earned = hourly_rate * duration_hours
        
        # Convert to NOS
        if nos_price_usd and nos_price_usd > 0:
            nos_payment = usd_earned / nos_price_usd
            return nos_payment
        
        return None
    except Exception as e:
        logger.error(f"Error calculating job payment: {str(e)}")
        return None


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"


async def save_job_earnings(user_id: str, node_address: str, node_name: str, duration_seconds: int, nos_earned: float, usd_value: float):
    """Save job earnings to database for statistics tracking"""
    try:
        now = datetime.now(timezone.utc)
        
        # Check if this is the first earning for this node
        tracking_meta = await db.node_tracking_metadata.find_one({
            "node_id": node_address,
            "user_id": user_id
        })
        
        if not tracking_meta:
            # First earnings record - initialize tracking metadata
            tracking_meta = {
                "node_id": node_address,
                "user_id": user_id,
                "tracking_started": now.isoformat(),
                "current_year_start": now.isoformat(),
                "archived_years": []
            }
            await db.node_tracking_metadata.insert_one(tracking_meta)
            logger.info(f"📊 Started earnings tracking for {node_name}")
        else:
            # Check if year cycle is complete
            tracking_start = datetime.fromisoformat(tracking_meta['current_year_start'].replace('Z', '+00:00'))
            years_diff = (now - tracking_start).days / 365.25
            
            if years_diff >= 1.0:
                # Year cycle complete - archive and reset
                year_end = tracking_start + timedelta(days=365)
                
                # Calculate year total
                year_earnings = await db.job_earnings.aggregate([
                    {
                        "$match": {
                            "node_id": node_address,
                            "user_id": user_id,
                            "completed_at": {
                                "$gte": tracking_start.isoformat(),
                                "$lt": year_end.isoformat()
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_nos": {"$sum": "$nos_earned"},
                            "total_usd": {"$sum": "$usd_value"},
                            "total_jobs": {"$sum": 1}
                        }
                    }
                ]).to_list(1)
                
                if year_earnings:
                    archive_entry = {
                        "year_number": len(tracking_meta.get('archived_years', [])) + 1,
                        "start_date": tracking_start.isoformat(),
                        "end_date": year_end.isoformat(),
                        "total_nos": year_earnings[0]['total_nos'],
                        "total_usd": year_earnings[0]['total_usd'],
                        "total_jobs": year_earnings[0]['total_jobs']
                    }
                    
                    # Keep only last 3 years
                    archived_years = tracking_meta.get('archived_years', [])
                    archived_years.append(archive_entry)
                    if len(archived_years) > 3:
                        archived_years = archived_years[-3:]
                    
                    # Update metadata for new year
                    await db.node_tracking_metadata.update_one(
                        {"node_id": node_address, "user_id": user_id},
                        {
                            "$set": {
                                "current_year_start": now.isoformat(),
                                "archived_years": archived_years
                            }
                        }
                    )
                    
                    logger.info(f"📊 Archived Year {archive_entry['year_number']} for {node_name}: {archive_entry['total_nos']:.2f} NOS")
        
        # Save earnings record
        earnings_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "node_id": node_address,
            "node_name": node_name,
            "completed_at": now.isoformat(),
            "duration_seconds": duration_seconds,
            "nos_earned": nos_earned,
            "usd_value": usd_value,
            "date": now.strftime("%Y-%m-%d"),  # For daily queries
            "month": now.strftime("%Y-%m"),     # For monthly queries
            "year": now.strftime("%Y")          # For yearly queries
        }
        
        await db.job_earnings.insert_one(earnings_record)
        logger.info(f"💾 Saved earnings: {nos_earned:.2f} NOS for {node_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving job earnings: {str(e)}")
        return False


async def send_notification_to_user(user_id: str, title: str, body: str, node_address: str = None, skip_telegram: bool = False):
    """Helper function to send push notification to user"""
    try:
        logger.info(f"=" * 70)
        logger.info(f"🔔 SENDING NOTIFICATION to user: {user_id}")
        logger.info(f"   Title: {title}")
        logger.info(f"   Body: {body}")
        logger.info(f"   Node: {node_address or 'N/A'}")
        logger.info(f"   Skip Telegram: {skip_telegram}")
        
        # Get user's device tokens
        tokens = await db.device_tokens.find({"user_id": user_id}).to_list(100)
        logger.info(f"   Found {len(tokens)} device token(s)")
        
        if not tokens:
            logger.warning(f"⚠️  No device tokens found for user {user_id}")
            logger.info(f"=" * 70)
            return
        
        # Get user preferences
        prefs = await db.notification_preferences.find_one({"user_id": user_id})
        if not prefs:
            prefs = {"vibration": True, "sound": True}
        
        # Send to all user devices
        for device in tokens:
            try:
                # Build notification with lock screen visibility
                notification = messaging.Notification(
                    title=title,
                    body=body
                )
                
                # Build data payload
                data = {
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "click_action": "/"
                }
                if node_address:
                    data["node_address"] = node_address
                
                # Build Android config with HIGH PRIORITY for lock screen
                android_config = messaging.AndroidConfig(
                    priority="high",  # HIGH PRIORITY - Shows on lock screen
                    notification=messaging.AndroidNotification(
                        sound="default" if prefs.get('sound', True) else None,
                        vibrate_timings_millis=[300, 100, 300, 100, 300] if prefs.get('vibration', True) else None,
                        priority="high",  # HIGH PRIORITY
                        visibility="public",  # Show full notification on lock screen
                        default_sound=True if prefs.get('sound', True) else False,
                        default_vibrate_timings=False,  # Use custom vibration
                        notification_priority="PRIORITY_HIGH"  # Ensure high priority
                    )
                )
                
                # Build APNS (iOS) config with HIGH PRIORITY
                apns_config = messaging.APNSConfig(
                    headers={
                        "apns-priority": "10",  # Maximum priority for iOS
                        "apns-push-type": "alert"
                    },
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body
                            ),
                            badge=1,
                            sound="default" if prefs.get('sound', True) else None,
                            content_available=True,  # Wake up the device
                            mutable_content=True  # Allow notification modifications
                        )
                    )
                )
                
                # Build WebPush config for PWA
                webpush_config = messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon="/logo192.png",
                        badge="/favicon-32x32.png",
                        vibrate=[300, 100, 300, 100, 300] if prefs.get('vibration', True) else [0],
                        require_interaction=False,  # Auto-dismiss after time
                        tag="nosana-node-alert",  # Group notifications
                        renotify=True  # Alert even if same tag
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link="/"  # URL to open when clicked
                    )
                )
                
                message = messaging.Message(
                    notification=notification,
                    data=data,
                    android=android_config,
                    apns=apns_config,
                    webpush=webpush_config,
                    token=device['token']
                )
                
                response = messaging.send(message)
                logger.info(f"✅ Notification sent successfully!")
                logger.info(f"   FCM Response: {response}")
                logger.info(f"   Device token: {device['token'][:30]}...")
            except Exception as e:
                logger.error(f"❌ Failed to send notification to device: {str(e)}")
                # Remove invalid tokens
                if "invalid" in str(e).lower() or "not registered" in str(e).lower():
                    logger.warning(f"🗑️  Removing invalid token: {device['token'][:30]}...")
                    await db.device_tokens.delete_one({"token": device['token']})
        
        # Also send Telegram notification (unless skip_telegram is True)
        if not skip_telegram:
            telegram_message = f"🔔 **{title}**\n\n{body}"
            if node_address:
                telegram_message += f"\n\n[View Dashboard](https://dashboard.nosana.com/host/{node_address})"
            
            await send_telegram_notification(user_id, telegram_message)
        
        logger.info(f"=" * 70)
    except Exception as e:
        logger.error(f"=" * 70)
        logger.error(f"❌ ERROR in send_notification_to_user: {str(e)}")
        logger.error(f"=" * 70)


@api_router.post("/nodes", response_model=Node)
@limiter.limit("20/minute")  # Rate limit node creation
async def add_node(request: Request, input: NodeCreate, current_user: User = Depends(get_current_user)):
    """Add a new node to monitor"""
    # Additional validation
    if not validate_solana_address(input.address):
        raise HTTPException(status_code=400, detail="Invalid Solana address format")
    
    # Check if node already exists for this user
    existing = await db.nodes.find_one({"address": input.address, "user_id": current_user.id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Node already exists")
    
    # Check user's node limit (prevent abuse)
    user_node_count = await db.nodes.count_documents({"user_id": current_user.id})
    if user_node_count >= 100:  # Limit to 100 nodes per user
        raise HTTPException(status_code=400, detail="Maximum node limit reached (100 nodes)")
    
    node_dict = input.model_dump()
    node_dict['user_id'] = current_user.id  # Associate with current user
    node_obj = Node(**node_dict)
    
    doc = node_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['last_updated'] = doc['last_updated'].isoformat()
    
    await db.nodes.insert_one(doc)
    
    logger.info(f"Node added by {current_user.email}: {input.address[:8]}...")
    
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
@limiter.limit("30/minute")  # Rate limit status checks
async def check_node_status_blockchain(request: Request, address: str):
    """Check node status from Solana blockchain"""
    # Validate address format
    if not validate_solana_address(address):
        raise HTTPException(status_code=400, detail="Invalid Solana address format")
    
    status_data = await fetch_node_status_from_solana(address)
    return status_data


@api_router.post("/nodes/refresh-all-status")
@limiter.limit("10/minute")  # Rate limit bulk refresh
async def refresh_all_nodes_status(request: Request, current_user: User = Depends(get_current_user)):
    """Automatically refresh status for all nodes from Solana blockchain"""
    nodes = await db.nodes.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    updated_count = 0
    errors = []
    
    # Get user notification preferences
    prefs = await db.notification_preferences.find_one({"user_id": current_user.id})
    if not prefs:
        prefs = {
            "notify_offline": True,
            "notify_online": True,
            "notify_job_started": True,
            "notify_job_completed": True
        }
    
    for node in nodes:
        try:
            address = node['address']
            previous_status = node.get('status', 'unknown')
            previous_job_status = node.get('job_status', 'unknown')
            
            # Fetch status from Solana
            status_data = await fetch_node_status_from_solana(address)
            current_status = status_data['status']
            current_job_status = status_data.get('job_status', 'unknown')
            
            # Update node in database
            await db.nodes.update_one(
                {"address": address, "user_id": current_user.id},
                {"$set": {
                    "status": current_status,
                    "job_status": current_job_status,
                    "sol_balance": status_data.get('sol_balance'),
                    "nos_balance": status_data.get('nos_balance'),
                    "total_jobs": status_data.get('total_jobs'),
                    "availability_score": status_data.get('availability_score'),
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            updated_count += 1
            
            # Send notifications on status changes
            node_name = node.get('name') or f"{address[:8]}..."
            
            # Log status changes
            if previous_status != current_status:
                logger.info(f"Node {node_name} status changed: {previous_status} -> {current_status}")
            if previous_job_status != current_job_status:
                logger.info(f"Node {node_name} job status changed: {previous_job_status} -> {current_job_status}")
            
            # Notify on offline
            if previous_status == 'online' and current_status == 'offline' and prefs.get('notify_offline', True):
                logger.info(f"Sending offline notification for {node_name}")
                await send_notification_to_user(
                    current_user.id,
                    "⚠️ Node Went Offline",
                    f"{node_name} is now OFFLINE",
                    address
                )
            
            # Notify on online
            elif previous_status == 'offline' and current_status == 'online' and prefs.get('notify_online', True):
                logger.info(f"Sending online notification for {node_name}")
                await send_notification_to_user(
                    current_user.id,
                    "✅ Node Back Online",
                    f"{node_name} is back ONLINE",
                    address
                )
            
            # Notify on job started - STORE START TIME
            if previous_job_status in ['idle', 'unknown', 'queue'] and current_job_status == 'running' and prefs.get('notify_job_started', True):
                logger.info(f"Sending job started notification for {node_name}")
                
                # Store job start time for duration calculation later
                job_start_time = datetime.now(timezone.utc).isoformat()
                await db.nodes.update_one(
                    {"address": address, "user_id": current_user.id},
                    {"$set": {"job_start_time": job_start_time}}
                )
                logger.info(f"📝 Stored job start time for {node_name}: {job_start_time}")
                
                await send_notification_to_user(
                    current_user.id,
                    "🚀 Job Started",
                    f"{node_name} started processing a job",
                    address
                )
            
            # Notify on job completed - WITH DURATION AND PAYMENT INFO
            elif previous_job_status == 'running' and current_job_status in ['idle', 'queue'] and prefs.get('notify_job_completed', True):
                logger.info(f"Sending job completed notification for {node_name}")
                
                # Calculate job duration and payment
                job_start_time = node.get('job_start_time')
                duration_str = "Unknown"
                payment_str = ""
                
                if job_start_time:
                    try:
                        # Parse start time
                        if isinstance(job_start_time, str):
                            start_dt = datetime.fromisoformat(job_start_time.replace('Z', '+00:00'))
                        else:
                            start_dt = job_start_time
                        
                        # Calculate duration
                        end_dt = datetime.now(timezone.utc)
                        duration_seconds = int((end_dt - start_dt).total_seconds())
                        duration_str = format_duration(duration_seconds)
                        
                        logger.info(f"⏱️ Job duration for {node_name}: {duration_str} ({duration_seconds}s)")
                        
                        # Get NOS price and calculate payment
                        nos_price = await get_nos_token_price()
                        if nos_price:
                            # Get GPU type from node (default to 3090 if not set)
                            gpu_type = node.get('gpu_type', '3090')
                            
                            # Calculate payment based on GPU type and duration
                            nos_payment = calculate_job_payment(duration_seconds, nos_price, gpu_type=gpu_type)
                            if nos_payment:
                                usd_value = nos_payment * nos_price
                                payment_str = f"\n💰 Payment: {nos_payment:.2f} NOS (~${usd_value:.2f} USD)"
                                logger.info(f"💰 Payment for {node_name}: {nos_payment:.2f} NOS (~${usd_value:.2f}) [GPU: {gpu_type}]")
                                
                                # Save earnings to statistics
                                await save_job_earnings(
                                    user_id=current_user.id,
                                    node_address=address,
                                    node_name=node_name,
                                    duration_seconds=duration_seconds,
                                    nos_earned=nos_payment,
                                    usd_value=usd_value
                                )
                        
                        # Increment completed jobs counter
                        job_count_completed = node.get('job_count_completed', 0) + 1
                        await db.nodes.update_one(
                            {"address": address, "user_id": current_user.id},
                            {"$set": {
                                "job_start_time": None,  # Clear start time
                                "job_count_completed": job_count_completed
                            }}
                        )
                        
                    except Exception as calc_error:
                        logger.error(f"Error calculating job stats: {str(calc_error)}")
                
                # Send notification via Firebase push (basic) - skip Telegram as we send enhanced version below
                await send_notification_to_user(
                    current_user.id,
                    "✅ Job Completed",
                    f"{node_name} completed a job",
                    address,
                    skip_telegram=True  # Skip Telegram, send enhanced version below
                )
                
                # Send ENHANCED notification via Telegram ONLY (with duration & payment)
                telegram_message = f"🎉 **Job Completed - {node_name}**\n\n"
                telegram_message += f"⏱️ Duration: {duration_str}"
                telegram_message += payment_str
                telegram_message += f"\n\n[View Dashboard](https://dashboard.nosana.com/host/{address})"
                
                try:
                    await send_telegram_notification(current_user.id, telegram_message)
                    logger.info(f"✅ Enhanced Telegram notification sent for {node_name}")
                except Exception as tg_error:
                    logger.error(f"Failed to send enhanced Telegram notification: {str(tg_error)}")
            
            # Check for LOW SOL BALANCE (critical for node operation)
            sol_balance = status_data.get('sol_balance')
            previous_sol_balance = node.get('sol_balance')
            
            # Alert if SOL balance drops below 0.006 (critical threshold)
            if sol_balance is not None and sol_balance < 0.006:
                # Only send if we haven't sent alert in last 24 hours
                last_alert = node.get('last_low_balance_alert')
                should_alert = True
                
                if last_alert:
                    from datetime import datetime as dt
                    try:
                        if isinstance(last_alert, str):
                            last_alert_time = dt.fromisoformat(last_alert.replace('Z', '+00:00'))
                        else:
                            last_alert_time = last_alert
                        
                        hours_since_alert = (datetime.now(timezone.utc) - last_alert_time).total_seconds() / 3600
                        should_alert = hours_since_alert >= 24  # Send max once per 24 hours
                    except:
                        should_alert = True
                
                if should_alert:
                    logger.info(f"⚠️ CRITICAL: Low SOL balance detected for {node_name}: {sol_balance:.6f} SOL")
                    
                    # Send notification with critical warning
                    await send_notification_to_user(
                        current_user.id,
                        "🟡 CRITICAL: Low SOL Balance",
                        f"{node_name} has only {sol_balance:.6f} SOL (minimum: 0.005). Top up immediately!",
                        address
                    )
                    
                    # Record alert time
                    await db.nodes.update_one(
                        {"address": address, "user_id": current_user.id},
                        {"$set": {"last_low_balance_alert": datetime.now(timezone.utc).isoformat()}}
                    )
            
        except Exception as e:
            errors.append({"address": node['address'], "error": str(e)})
            logger.error(f"Error updating node {node['address']}: {str(e)}")
    
    logger.info(f"Refreshed {updated_count} nodes for user {current_user.email}")
    
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



# ===========================
# Earnings Statistics Endpoints
# ===========================

@api_router.get("/earnings/node/{address}/yesterday")
async def get_yesterday_earnings(address: str, current_user: User = Depends(get_current_user)):
    """Get yesterday's earnings for a node"""
    try:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await db.job_earnings.aggregate([
            {
                "$match": {
                    "node_id": address,
                    "user_id": current_user.id,
                    "date": yesterday
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_nos": {"$sum": "$nos_earned"},
                    "total_usd": {"$sum": "$usd_value"},
                    "total_jobs": {"$sum": 1},
                    "total_duration": {"$sum": "$duration_seconds"}
                }
            }
        ]).to_list(1)
        
        if result:
            return {
                "date": yesterday,
                "nos_earned": round(result[0]['total_nos'], 2),
                "usd_value": round(result[0]['total_usd'], 2),
                "job_count": result[0]['total_jobs'],
                "duration_seconds": result[0]['total_duration']
            }
        else:
            return {
                "date": yesterday,
                "nos_earned": 0,
                "usd_value": 0,
                "job_count": 0,
                "duration_seconds": 0
            }
    
    except Exception as e:
        logger.error(f"Error getting yesterday earnings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get earnings")


@api_router.get("/earnings/node/{address}/today")
async def get_today_earnings(address: str, current_user: User = Depends(get_current_user)):
    """Get today's earnings for a node (in progress)"""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        result = await db.job_earnings.aggregate([
            {
                "$match": {
                    "node_id": address,
                    "user_id": current_user.id,
                    "date": today
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_nos": {"$sum": "$nos_earned"},
                    "total_usd": {"$sum": "$usd_value"},
                    "total_jobs": {"$sum": 1},
                    "total_duration": {"$sum": "$duration_seconds"}
                }
            }
        ]).to_list(1)
        
        if result:
            return {
                "date": today,
                "nos_earned": round(result[0]['total_nos'], 2),
                "usd_value": round(result[0]['total_usd'], 2),
                "job_count": result[0]['total_jobs'],
                "duration_seconds": result[0]['total_duration']
            }
        else:
            return {
                "date": today,
                "nos_earned": 0,
                "usd_value": 0,
                "job_count": 0,
                "duration_seconds": 0
            }
    
    except Exception as e:
        logger.error(f"Error getting today earnings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get earnings")


@api_router.get("/earnings/node/{address}/monthly")
async def get_monthly_earnings(address: str, current_user: User = Depends(get_current_user)):
    """Get monthly breakdown of earnings"""
    try:
        # Get tracking metadata
        tracking_meta = await db.node_tracking_metadata.find_one({
            "node_id": address,
            "user_id": current_user.id
        })
        
        if not tracking_meta:
            return {
                "tracking_started": None,
                "months": []
            }
        
        tracking_start = datetime.fromisoformat(tracking_meta['tracking_started'].replace('Z', '+00:00'))
        current_year_start = datetime.fromisoformat(tracking_meta['current_year_start'].replace('Z', '+00:00'))
        
        # Get all months from tracking start to now
        monthly_earnings = await db.job_earnings.aggregate([
            {
                "$match": {
                    "node_id": address,
                    "user_id": current_user.id,
                    "completed_at": {"$gte": current_year_start.isoformat()}
                }
            },
            {
                "$group": {
                    "_id": "$month",
                    "total_nos": {"$sum": "$nos_earned"},
                    "total_usd": {"$sum": "$usd_value"},
                    "total_jobs": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": -1}  # Sort by month descending
            }
        ]).to_list(100)
        
        months = []
        for month_data in monthly_earnings:
            year, month = month_data['_id'].split('-')
            # Get first and last day of month
            first_day = datetime(int(year), int(month), 1)
            if int(month) == 12:
                last_day = datetime(int(year) + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(int(year), int(month) + 1, 1) - timedelta(days=1)
            
            # Check if this is the first month (partial)
            is_first_month = (first_day.year == tracking_start.year and first_day.month == tracking_start.month)
            
            months.append({
                "month": month_data['_id'],
                "start_date": tracking_start.strftime("%Y-%m-%d") if is_first_month else first_day.strftime("%Y-%m-%d"),
                "end_date": last_day.strftime("%Y-%m-%d"),
                "nos_earned": round(month_data['total_nos'], 2),
                "usd_value": round(month_data['total_usd'], 2),
                "job_count": month_data['total_jobs'],
                "is_current": month_data['_id'] == datetime.now(timezone.utc).strftime("%Y-%m"),
                "is_partial": is_first_month
            })
        
        return {
            "tracking_started": tracking_start.strftime("%Y-%m-%d"),
            "months": months
        }
    
    except Exception as e:
        logger.error(f"Error getting monthly earnings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get monthly earnings")


@api_router.get("/earnings/node/{address}/yearly")
async def get_yearly_earnings(address: str, current_user: User = Depends(get_current_user)):
    """Get current year total and archived years"""
    try:
        # Get tracking metadata
        tracking_meta = await db.node_tracking_metadata.find_one({
            "node_id": address,
            "user_id": current_user.id
        })
        
        if not tracking_meta:
            return {
                "current_year": None,
                "archived_years": []
            }
        
        tracking_start = datetime.fromisoformat(tracking_meta['tracking_started'].replace('Z', '+00:00'))
        current_year_start = datetime.fromisoformat(tracking_meta['current_year_start'].replace('Z', '+00:00'))
        
        # Calculate current year total
        year_end = current_year_start + timedelta(days=365)
        current_year_earnings = await db.job_earnings.aggregate([
            {
                "$match": {
                    "node_id": address,
                    "user_id": current_user.id,
                    "completed_at": {
                        "$gte": current_year_start.isoformat(),
                        "$lt": year_end.isoformat()
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_nos": {"$sum": "$nos_earned"},
                    "total_usd": {"$sum": "$usd_value"},
                    "total_jobs": {"$sum": 1}
                }
            }
        ]).to_list(1)
        
        # Calculate months completed and remaining
        now = datetime.now(timezone.utc)
        months_elapsed = (now.year - current_year_start.year) * 12 + now.month - current_year_start.month
        if now.day < current_year_start.day:
            months_elapsed -= 1
        months_remaining = max(0, 12 - months_elapsed)
        
        current_year = {
            "year_number": len(tracking_meta.get('archived_years', [])) + 1,
            "start_date": current_year_start.strftime("%Y-%m-%d"),
            "end_date": year_end.strftime("%Y-%m-%d"),
            "nos_earned": round(current_year_earnings[0]['total_nos'], 2) if current_year_earnings else 0,
            "usd_value": round(current_year_earnings[0]['total_usd'], 2) if current_year_earnings else 0,
            "job_count": current_year_earnings[0]['total_jobs'] if current_year_earnings else 0,
            "months_completed": months_elapsed + 1,
            "months_remaining": months_remaining
        }
        
        return {
            "current_year": current_year,
            "archived_years": tracking_meta.get('archived_years', [])
        }
    
    except Exception as e:
        logger.error(f"Error getting yearly earnings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get yearly earnings")


@api_router.get("/earnings/node/{address}/live")
async def get_live_earnings_from_dashboard(address: str, current_user: User = Depends(get_current_user)):
    """
    Get real-time earnings by scraping Nosana dashboard AND store the data
    Returns actual job payment data from the live dashboard
    """
    try:
        # Verify node belongs to user
        node = await db.nodes.find_one({
            "address": address,
            "user_id": current_user.id
        })
        
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Scrape live data from Nosana dashboard
        jobs = await scrape_nosana_job_history(address)
        
        # Store scraped jobs in database
        if jobs:
            await store_scraped_jobs(current_user.id, address, jobs)
        
        if not jobs:
            return {
                "node_address": address,
                "jobs": [],
                "summary": {
                    "total_jobs": 0,
                    "total_usd": 0,
                    "total_nos": 0,
                    "completed_jobs": 0,
                    "running_jobs": 0
                }
            }
        
        # Get current NOS price
        nos_price = fetch_nos_price_coingecko()
        if not nos_price:
            nos_price = 0.1  # Fallback price
        
        # Calculate earnings for each job
        total_usd = 0
        completed_jobs = 0
        running_jobs = 0
        
        for job in jobs:
            # Calculate USD earned for this job
            duration_hours = job['duration_seconds'] / 3600.0
            usd_earned = duration_hours * job['hourly_rate_usd']
            job['usd_earned'] = round(usd_earned, 4)
            job['nos_earned'] = round(usd_earned / nos_price, 2) if nos_price > 0 else 0
            
            # Convert datetime to string for JSON serialization
            if isinstance(job['started'], datetime):
                job['started'] = job['started'].isoformat()
            
            # Add to totals (only count completed jobs in total)
            if job['status'] == 'SUCCESS':
                total_usd += usd_earned
                completed_jobs += 1
            else:
                running_jobs += 1
        
        total_nos = round(total_usd / nos_price, 2) if nos_price > 0 else 0
        
        return {
            "node_address": address,
            "nos_price": nos_price,
            "jobs": jobs,
            "summary": {
                "total_jobs": len(jobs),
                "total_usd": round(total_usd, 2),
                "total_nos": total_nos,
                "completed_jobs": completed_jobs,
                "running_jobs": running_jobs
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting live earnings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get live earnings from dashboard")


# Include the router in the main app
app.include_router(api_router)

# CORS middleware with more restrictive settings
allowed_origins = os.environ.get('CORS_ORIGINS', '*')
if allowed_origins == '*':
    logger.warning("CORS set to allow all origins. Set CORS_ORIGINS environment variable for production.")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins.split(',') if allowed_origins != '*' else ['*'],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Global exception handler for better error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent information leakage"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Don't expose internal errors to users
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint - also keeps Nosana service awake"""
    try:
        # Ping Nosana service to keep it alive
        requests.get("http://localhost:3001/health", timeout=2)
    except:
        pass  # Don't fail health check if Nosana service is down
    
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()