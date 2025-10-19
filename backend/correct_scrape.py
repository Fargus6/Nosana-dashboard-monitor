#!/usr/bin/env python3
"""
Correct scraping with proper day boundaries
"""
import asyncio
import sys
sys.path.append('/app/backend')

from datetime import datetime, timezone, timedelta
import os
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'
os.environ['MONGO_URL'] = 'mongodb://mongo:27017'

from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorClient
import re
import uuid

# MongoDB connection
client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client.test_database

async def parse_relative_time_correct(time_text: str, scrape_time: datetime) -> datetime:
    """Convert relative time like '3 hours ago' to datetime"""
    try:
        hours_match = re.search(r'(\d+)\s+hours?\s+ago', time_text)
        if hours_match:
            return scrape_time - timedelta(hours=int(hours_match.group(1)))
        
        minutes_match = re.search(r'(\d+)\s+minutes?\s+ago', time_text)
        if minutes_match:
            return scrape_time - timedelta(minutes=int(minutes_match.group(1)))
        
        return scrape_time
    except Exception as e:
        print(f"Error parsing relative time '{time_text}': {str(e)}")
        return scrape_time

async def scrape_and_store():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    user_id = "52aa0708-e317-4437-9ac4-fbb7262f6071"  # Your user ID
    
    scrape_time = datetime.now(timezone.utc)
    print(f"\n🕐 Scrape time: {scrape_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"🌐 Scraping Nosana dashboard for: {node_address}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        url = f"https://dashboard.nosana.com/host/{node_address}"
        await page.goto(url, wait_until='networkidle', timeout=15000)
        await page.wait_for_selector('table', timeout=10000)
        
        # Extract jobs
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
        
        print(f"\n📊 Found {len(jobs_data)} jobs on dashboard")
        print("="*100)
        
        # NOS price
        nos_price = 0.476626
        
        # Today's boundaries (UTC)
        today_start = scrape_time.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        print(f"\n📅 Today starts at: {today_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 Yesterday was: {yesterday_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("="*100)
        
        today_jobs = []
        yesterday_jobs = []
        
        for idx, job in enumerate(jobs_data, 1):
            # Parse duration
            duration_seconds = 0
            duration_text = job['duration']
            
            hours_match = re.search(r'(\d+)h', duration_text)
            if hours_match:
                duration_seconds += int(hours_match.group(1)) * 3600
            
            minutes_match = re.search(r'(\d+)m', duration_text)
            if minutes_match:
                duration_seconds += int(minutes_match.group(1)) * 60
            
            seconds_match = re.search(r'(\d+)s', duration_text)
            if seconds_match:
                duration_seconds += int(seconds_match.group(1))
            
            # Parse hourly rate
            rate_str = job['price'].replace('/h', '').replace('$', '').strip()
            hourly_rate = float(rate_str)
            
            # Calculate started time (from relative time)
            started_time = await parse_relative_time_correct(job['started'], scrape_time)
            
            # Calculate completed time
            if job['status'] == 'SUCCESS':
                completed_time = started_time + timedelta(seconds=duration_seconds)
            else:
                completed_time = None
            
            # Calculate earnings
            duration_hours = duration_seconds / 3600.0
            usd_earned = duration_hours * hourly_rate
            nos_earned = usd_earned / nos_price
            
            # Determine which day
            if completed_time:
                if completed_time >= today_start:
                    day = "TODAY"
                    today_jobs.append(job)
                elif completed_time >= yesterday_start:
                    day = "YESTERDAY"
                    yesterday_jobs.append(job)
                else:
                    day = "OLDER"
            else:
                day = "RUNNING"
            
            print(f"\nJob #{idx}: {job['job_id'][:12]}...")
            print(f"  Started: {job['started']} → {started_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if completed_time:
                print(f"  Completed: {completed_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Duration: {duration_text}")
            print(f"  Rate: ${hourly_rate}/h")
            print(f"  Status: {job['status']}")
            print(f"  Day: {day}")
            print(f"  💰 USD: ${usd_earned:.4f} | NOS: {nos_earned:.2f}")
            
            # Store in database
            if job['status'] == 'SUCCESS':
                job_doc = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "node_address": node_address,
                    "job_id": job['job_id'],
                    "started": started_time.isoformat(),
                    "started_text": job['started'],
                    "completed": completed_time.isoformat() if completed_time else None,
                    "duration_seconds": duration_seconds,
                    "duration_text": duration_text,
                    "hourly_rate_usd": hourly_rate,
                    "usd_earned": round(usd_earned, 4),
                    "nos_earned": round(nos_earned, 2),
                    "nos_price_at_time": nos_price,
                    "gpu_type": job['gpu'],
                    "status": job['status'],
                    "scraped_at": scrape_time.isoformat()
                }
                
                await db.scraped_jobs.insert_one(job_doc)
        
        # Calculate totals
        today_total = sum(
            (int(re.search(r'(\d+)m', j['duration']).group(1)) * 60 + 
             int(re.search(r'(\d+)s', j['duration']).group(1))) / 3600.0 * 
            float(j['price'].replace('/h', '').replace('$', '').strip())
            for j in today_jobs
        )
        
        yesterday_total = sum(
            (int(re.search(r'(\d+)m', j['duration']).group(1)) * 60 + 
             int(re.search(r'(\d+)s', j['duration']).group(1))) / 3600.0 * 
            float(j['price'].replace('/h', '').replace('$', '').strip())
            for j in yesterday_jobs
        )
        
        print("\n" + "="*100)
        print("📊 SUMMARY BY CALENDAR DAY")
        print("="*100)
        print(f"\n📅 TODAY ({today_start.strftime('%Y-%m-%d')}):")
        print(f"   Jobs: {len(today_jobs)}")
        print(f"   Total: ${today_total:.2f} USD | {today_total/nos_price:.2f} NOS")
        
        print(f"\n📅 YESTERDAY ({yesterday_start.strftime('%Y-%m-%d')}):")
        print(f"   Jobs: {len(yesterday_jobs)}")
        print(f"   Total: ${yesterday_total:.2f} USD | {yesterday_total/nos_price:.2f} NOS")
        print("="*100)
        
        print(f"\n✅ Stored {len(today_jobs) + len(yesterday_jobs)} jobs in database")

if __name__ == "__main__":
    asyncio.run(scrape_and_store())
