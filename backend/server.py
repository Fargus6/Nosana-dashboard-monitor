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
from bs4 import BeautifulSoup
import re
from playwright.async_api import async_playwright
import asyncio


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
    last_status: Optional[str] = None  # online, offline
    last_job_status: Optional[str] = None  # running, queue, idle
    last_checked: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NodeCreate(BaseModel):
    address: str
    name: Optional[str] = None

class NodeStatus(BaseModel):
    address: str
    status: str  # online, offline, error
    job_status: Optional[str] = None  # running, queue, idle
    job_count: Optional[int] = None
    last_checked: datetime
    status_changed: bool = False


async def scrape_node_status(address: str) -> dict:
    """Scrape node status from Nosana dashboard using Playwright"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = f"https://dashboard.nosana.com/host/{address}"
            
            # Navigate to page with timeout
            try:
                response = await page.goto(url, wait_until='networkidle', timeout=15000)
                
                # Check if page returned 404 or error
                if response and response.status == 404:
                    await browser.close()
                    return {
                        'status': 'error',
                        'job_status': None,
                        'job_count': 0
                    }
                
                # Wait for content to load
                await page.wait_for_timeout(2000)
                
                # Get page text content
                page_text = await page.text_content('body')
                page_text_lower = page_text.lower() if page_text else ''
                
                # Check for error states
                if 'not found' in page_text_lower or 'error' in page_text_lower:
                    await browser.close()
                    return {
                        'status': 'error',
                        'job_status': None,
                        'job_count': 0
                    }
                
                # Determine status based on page content
                status = 'online'  # Default
                job_status = 'idle'
                job_count = 0
                
                # Check for status indicators
                if 'offline' in page_text_lower:
                    status = 'offline'
                elif 'online' in page_text_lower or 'active' in page_text_lower:
                    status = 'online'
                
                # Check for job status
                if 'running' in page_text_lower:
                    job_status = 'running'
                elif 'queue' in page_text_lower or 'queued' in page_text_lower:
                    job_status = 'queue'
                
                # Try to extract job count
                if page_text:
                    job_matches = re.findall(r'(\d+)\s*job', page_text_lower)
                    if job_matches:
                        job_count = int(job_matches[0])
                
                await browser.close()
                
                return {
                    'status': status,
                    'job_status': job_status,
                    'job_count': job_count
                }
                
            except Exception as e:
                await browser.close()
                logger.error(f"Error navigating to {url}: {str(e)}")
                return {
                    'status': 'offline',
                    'job_status': None,
                    'job_count': 0
                }
        
    except Exception as e:
        logger.error(f"Error scraping node {address}: {str(e)}")
        return {
            'status': 'error',
            'job_status': None,
            'job_count': 0
        }


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
    if doc['last_checked']:
        doc['last_checked'] = doc['last_checked'].isoformat()
    
    await db.nodes.insert_one(doc)
    return node_obj


@api_router.get("/nodes", response_model=List[Node])
async def get_nodes():
    """Get all monitored nodes"""
    nodes = await db.nodes.find({}, {"_id": 0}).to_list(1000)
    
    for node in nodes:
        if isinstance(node.get('created_at'), str):
            node['created_at'] = datetime.fromisoformat(node['created_at'])
        if isinstance(node.get('last_checked'), str):
            node['last_checked'] = datetime.fromisoformat(node['last_checked'])
    
    return nodes


@api_router.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    """Delete a node"""
    result = await db.nodes.delete_one({"id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node deleted successfully"}


@api_router.get("/nodes/{address}/status", response_model=NodeStatus)
async def get_node_status(address: str):
    """Get current status of a specific node"""
    # Get previous status from DB
    node = await db.nodes.find_one({"address": address}, {"_id": 0})
    previous_status = node.get('last_status') if node else None
    
    # Scrape current status
    scraped_data = await scrape_node_status(address)
    current_status = scraped_data['status']
    
    # Check if status changed from online to offline
    status_changed = False
    if previous_status == 'online' and current_status == 'offline':
        status_changed = True
    
    # Update node in DB
    if node:
        await db.nodes.update_one(
            {"address": address},
            {"$set": {
                "last_status": current_status,
                "last_job_status": scraped_data['job_status'],
                "last_checked": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    return NodeStatus(
        address=address,
        status=current_status,
        job_status=scraped_data['job_status'],
        job_count=scraped_data['job_count'],
        last_checked=datetime.now(timezone.utc),
        status_changed=status_changed
    )


@api_router.get("/nodes/status/all", response_model=List[NodeStatus])
async def get_all_nodes_status():
    """Get current status of all monitored nodes"""
    nodes = await db.nodes.find({}, {"_id": 0}).to_list(1000)
    
    statuses = []
    for node in nodes:
        address = node['address']
        previous_status = node.get('last_status')
        
        # Scrape current status
        scraped_data = await scrape_node_status(address)
        current_status = scraped_data['status']
        
        # Check if status changed from online to offline
        status_changed = False
        if previous_status == 'online' and current_status == 'offline':
            status_changed = True
        
        # Update node in DB
        await db.nodes.update_one(
            {"address": address},
            {"$set": {
                "last_status": current_status,
                "last_job_status": scraped_data['job_status'],
                "last_checked": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        statuses.append(NodeStatus(
            address=address,
            status=current_status,
            job_status=scraped_data['job_status'],
            job_count=scraped_data['job_count'],
            last_checked=datetime.now(timezone.utc),
            status_changed=status_changed
        ))
    
    return statuses


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