from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import requests
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey
import base64
import struct

# Set Playwright browser path
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class Node(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: str
    name: Optional[str] = None
    status: str = "unknown"  # online, offline, unknown
    job_status: Optional[str] = None  # running, queue, idle
    notes: Optional[str] = None
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


@api_router.post("/nodes", response_model=Node)
async def add_node(input: NodeCreate):
    """Add a new node to monitor"""
    # Check if node already exists
    existing = await db.nodes.find_one({"address": input.address}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Node already exists")
    
    node_dict = input.model_dump()
    node_obj = Node(**node_dict)
    
    doc = node_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['last_updated'] = doc['last_updated'].isoformat()
    
    await db.nodes.insert_one(doc)
    return node_obj


@api_router.get("/nodes", response_model=List[Node])
async def get_nodes():
    """Get all monitored nodes"""
    nodes = await db.nodes.find({}, {"_id": 0}).to_list(1000)
    
    for node in nodes:
        if isinstance(node.get('created_at'), str):
            node['created_at'] = datetime.fromisoformat(node['created_at'])
        if isinstance(node.get('last_updated'), str):
            node['last_updated'] = datetime.fromisoformat(node['last_updated'])
    
    return nodes


@api_router.put("/nodes/{node_id}", response_model=Node)
async def update_node(node_id: str, update: NodeUpdate):
    """Update node information"""
    node = await db.nodes.find_one({"id": node_id}, {"_id": 0})
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    update_data = update.model_dump(exclude_none=True)
    update_data['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    await db.nodes.update_one(
        {"id": node_id},
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
async def delete_node(node_id: str):
    """Delete a node"""
    result = await db.nodes.delete_one({"id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node deleted successfully"}


@api_router.get("/nodes/{address}/check-status")
async def check_node_status_blockchain(address: str):
    """Check node status from Solana blockchain"""
    status_data = await fetch_node_status_from_solana(address)
    return status_data


@api_router.post("/nodes/refresh-all-status")
async def refresh_all_nodes_status():
    """Automatically refresh status for all nodes from Solana blockchain"""
    nodes = await db.nodes.find({}, {"_id": 0}).to_list(1000)
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
                {"address": address},
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