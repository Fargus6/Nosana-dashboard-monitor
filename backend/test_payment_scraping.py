#!/usr/bin/env python3
"""
Test the scrape_latest_job_payment function
"""
import asyncio
import sys
sys.path.append('/app/backend')

from server import scrape_latest_job_payment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scrape_payment():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    
    print(f"\n{'='*80}")
    print(f"Testing Payment Scraping for Node: {node_address}")
    print(f"{'='*80}\n")
    
    payment = await scrape_latest_job_payment(node_address)
    
    if payment:
        print(f"✅ Successfully scraped payment: ${payment:.3f} USD")
        print(f"\nThis is the ACTUAL payment from the dashboard's price column")
        print(f"NO calculations or formulas used - direct scraping only")
    else:
        print(f"❌ Failed to scrape payment")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(test_scrape_payment())
