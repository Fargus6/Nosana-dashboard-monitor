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

# Create the main app without a prefix
app = FastAPI()

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
                    return {
                        'job_status': data.get('jobStatus', 'idle'),
                        'nos_balance': None,
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
                
                # Extract NOS balance
                nos_balance = None
                nos_match = re.search(r'(\d+\.?\d*)\s*nos', text_lower)
                if nos_match:
                    nos_balance = float(nos_match.group(1))
                
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
                    'nos_balance': nos_balance,
                    'sol_balance': sol_balance,
                    'total_jobs': total_jobs,
                    'availability_score': availability_score
                }
                
            except Exception as page_error:
                await browser.close()
                logger.warning(f"Error scraping dashboard for {node_address[:8]}: {str(page_error)}")
                return {
                    'job_status': 'idle',
                    'nos_balance': None,
                    'sol_balance': None,
                    'total_jobs': None,
                    'availability_score': None
                }
            
    except Exception as e:
        logger.error(f"Error checking node jobs: {str(e)}")
        return {
            'job_status': 'idle',
            'nos_balance': None,
            'sol_balance': None,
            'total_jobs': None,
            'availability_score': None
        }


# Authentication endpoints
@api_router.post("/auth/register", response_model=Token)
@limiter.limit("5/hour")  # Limit registration attempts
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
        device_token = DeviceToken(
            token=token,
            user_id=current_user.id
        )
        
        # Check if token already exists
        existing = await db.device_tokens.find_one({"token": token})
        if existing:
            # Update existing
            await db.device_tokens.update_one(
                {"token": token},
                {"$set": {"user_id": current_user.id, "created_at": datetime.now(timezone.utc).isoformat()}}
            )
        else:
            # Insert new
            token_dict = device_token.model_dump()
            await db.device_tokens.insert_one(token_dict)
        
        logger.info(f"Device token registered for user {current_user.email}")
        return {"status": "success", "message": "Device token registered"}
    except Exception as e:
        logger.error(f"Error registering device token: {str(e)}")
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


async def send_notification_to_user(user_id: str, title: str, body: str, node_address: str = None):
    """Helper function to send push notification to user"""
    try:
        # Get user's device tokens
        tokens = await db.device_tokens.find({"user_id": user_id}).to_list(100)
        
        if not tokens:
            return
        
        # Get user preferences
        prefs = await db.notification_preferences.find_one({"user_id": user_id})
        if not prefs:
            prefs = {"vibration": True, "sound": True}
        
        # Send to all user devices
        for device in tokens:
            try:
                # Build notification
                notification = messaging.Notification(
                    title=title,
                    body=body
                )
                
                # Build data payload
                data = {
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                if node_address:
                    data["node_address"] = node_address
                
                # Build Android config with vibration/sound
                android_config = messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        sound="default" if prefs.get('sound', True) else None,
                        vibrate_timings_millis=[100, 200, 100] if prefs.get('vibration', True) else None
                    )
                )
                
                message = messaging.Message(
                    notification=notification,
                    data=data,
                    android=android_config,
                    token=device['token']
                )
                
                response = messaging.send(message)
                logger.info(f"Notification sent to {user_id}: {response}")
            except Exception as e:
                logger.error(f"Failed to send notification: {str(e)}")
                # Remove invalid tokens
                if "invalid" in str(e).lower() or "not registered" in str(e).lower():
                    await db.device_tokens.delete_one({"token": device['token']})
    except Exception as e:
        logger.error(f"Error in send_notification_to_user: {str(e)}")


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
            
            # Notify on offline
            if previous_status == 'online' and current_status == 'offline' and prefs.get('notify_offline', True):
                await send_notification_to_user(
                    current_user.id,
                    "⚠️ Node Went Offline",
                    f"{node_name} is now OFFLINE",
                    address
                )
            
            # Notify on online
            elif previous_status == 'offline' and current_status == 'online' and prefs.get('notify_online', True):
                await send_notification_to_user(
                    current_user.id,
                    "✅ Node Back Online",
                    f"{node_name} is back ONLINE",
                    address
                )
            
            # Notify on job started
            if previous_job_status in ['idle', 'unknown'] and current_job_status == 'running' and prefs.get('notify_job_started', True):
                await send_notification_to_user(
                    current_user.id,
                    "🚀 Job Started",
                    f"{node_name} started processing a job",
                    address
                )
            
            # Notify on job completed
            elif previous_job_status == 'running' and current_job_status in ['idle', 'queue'] and prefs.get('notify_job_completed', True):
                await send_notification_to_user(
                    current_user.id,
                    "✅ Job Completed",
                    f"{node_name} completed a job",
                    address
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
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()