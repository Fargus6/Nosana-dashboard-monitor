#!/usr/bin/env python3
"""
Populate sample earnings data for testing statistics feature
- Adds September 2025 complete month
- Adds yesterday's earnings
- Adds some October data
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.getenv('DB_NAME', 'test_database')

db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client[DB_NAME]


async def populate_sample_data():
    """Populate sample earnings data for all users and their nodes"""
    
    print("=" * 70)
    print("📊 Populating Sample Earnings Data")
    print("=" * 70)
    print()
    
    # Get all users and their nodes
    users = await db.users.find({}).to_list(100)
    
    if not users:
        print("❌ No users found. Please create an account first.")
        return
    
    print(f"Found {len(users)} user(s)")
    print()
    
    total_records = 0
    
    for user in users:
        user_id = user['id']
        email = user.get('email', 'Unknown')
        
        # Get user's nodes
        nodes = await db.nodes.find({"user_id": user_id}).to_list(100)
        
        if not nodes:
            print(f"⚠️  User {email} has no nodes. Skipping.")
            continue
        
        print(f"👤 User: {email}")
        print(f"   Nodes: {len(nodes)}")
        print()
        
        for node in nodes:
            node_address = node['address']
            node_name = node.get('name', 'Unnamed Node')
            
            print(f"   📡 {node_name} ({node_address[:10]}...)")
            
            # Check if data already exists
            existing = await db.job_earnings.count_documents({
                "node_id": node_address,
                "user_id": user_id
            })
            
            if existing > 0:
                print(f"      ⚠️  Already has {existing} earnings records. Skipping to avoid duplicates.")
                continue
            
            # Create tracking metadata
            tracking_start = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
            
            await db.node_tracking_metadata.insert_one({
                "node_id": node_address,
                "user_id": user_id,
                "tracking_started": tracking_start.isoformat(),
                "current_year_start": tracking_start.isoformat(),
                "archived_years": []
            })
            
            print(f"      ✅ Created tracking metadata (started: Sept 1, 2025)")
            
            # Generate sample earnings
            earnings_records = []
            
            # September 2025 (Sept 1-30)
            sept_jobs = 0
            for day in range(1, 31):  # Sept 1-30
                # Random number of jobs per day (2-12)
                jobs_per_day = random.randint(2, 12)
                
                for job in range(jobs_per_day):
                    # Random time during the day
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 9, day, hour, minute, 0, tzinfo=timezone.utc)
                    
                    # Random job duration (15 min to 3 hours)
                    duration_seconds = random.randint(900, 10800)
                    
                    # Random NOS price around $0.46
                    nos_price = random.uniform(0.42, 0.50)
                    
                    # Calculate earnings based on A100 rate ($0.90/hr)
                    hourly_rate = 0.90
                    duration_hours = duration_seconds / 3600.0
                    usd_earned = hourly_rate * duration_hours
                    nos_earned = usd_earned / nos_price
                    
                    earnings_records.append({
                        "user_id": user_id,
                        "node_id": node_address,
                        "node_name": node_name,
                        "completed_at": completed_at.isoformat(),
                        "duration_seconds": duration_seconds,
                        "nos_earned": nos_earned,
                        "usd_value": usd_earned,
                        "date": completed_at.strftime("%Y-%m-%d"),
                        "month": completed_at.strftime("%Y-%m"),
                        "year": completed_at.strftime("%Y")
                    })
                    
                    sept_jobs += 1
            
            # October 2025 - some days (Oct 1-18)
            oct_jobs = 0
            for day in range(1, 19):  # Oct 1-18
                jobs_per_day = random.randint(2, 10)
                
                for job in range(jobs_per_day):
                    hour = random.randint(0, 23)
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 10, day, hour, minute, 0, tzinfo=timezone.utc)
                    
                    duration_seconds = random.randint(900, 10800)
                    nos_price = random.uniform(0.44, 0.48)
                    
                    hourly_rate = 0.90
                    duration_hours = duration_seconds / 3600.0
                    usd_earned = hourly_rate * duration_hours
                    nos_earned = usd_earned / nos_price
                    
                    earnings_records.append({
                        "user_id": user_id,
                        "node_id": node_address,
                        "node_name": node_name,
                        "completed_at": completed_at.isoformat(),
                        "duration_seconds": duration_seconds,
                        "nos_earned": nos_earned,
                        "usd_value": usd_earned,
                        "date": completed_at.strftime("%Y-%m-%d"),
                        "month": completed_at.strftime("%Y-%m"),
                        "year": completed_at.strftime("%Y")
                    })
                    
                    oct_jobs += 1
            
            # Yesterday (specific date with more earnings for visibility)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            yesterday_jobs = 0
            
            for job in range(8):  # 8 jobs yesterday
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    yesterday.year, yesterday.month, yesterday.day,
                    hour, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(1800, 7200)  # 30min to 2hr
                nos_price = random.uniform(0.45, 0.47)
                
                hourly_rate = 0.90
                duration_hours = duration_seconds / 3600.0
                usd_earned = hourly_rate * duration_hours
                nos_earned = usd_earned / nos_price
                
                earnings_records.append({
                    "user_id": user_id,
                    "node_id": node_address,
                    "node_name": node_name,
                    "completed_at": completed_at.isoformat(),
                    "duration_seconds": duration_seconds,
                    "nos_earned": nos_earned,
                    "usd_value": usd_earned,
                    "date": completed_at.strftime("%Y-%m-%d"),
                    "month": completed_at.strftime("%Y-%m"),
                    "year": completed_at.strftime("%Y")
                })
                
                yesterday_jobs += 1
            
            # Today (a few jobs)
            today = datetime.now(timezone.utc)
            today_jobs = 0
            
            for job in range(3):  # 3 jobs today so far
                hour = random.randint(0, today.hour)
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    today.year, today.month, today.day,
                    hour, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(1200, 5400)
                nos_price = random.uniform(0.45, 0.47)
                
                hourly_rate = 0.90
                duration_hours = duration_seconds / 3600.0
                usd_earned = hourly_rate * duration_hours
                nos_earned = usd_earned / nos_price
                
                earnings_records.append({
                    "user_id": user_id,
                    "node_id": node_address,
                    "node_name": node_name,
                    "completed_at": completed_at.isoformat(),
                    "duration_seconds": duration_seconds,
                    "nos_earned": nos_earned,
                    "usd_value": usd_earned,
                    "date": completed_at.strftime("%Y-%m-%d"),
                    "month": completed_at.strftime("%Y-%m"),
                    "year": completed_at.strftime("%Y")
                })
                
                today_jobs += 1
            
            # Insert all earnings records
            if earnings_records:
                await db.job_earnings.insert_many(earnings_records)
                total_records += len(earnings_records)
                
                # Calculate totals
                sept_total = sum(r['nos_earned'] for r in earnings_records if r['month'] == '2025-09')
                oct_total = sum(r['nos_earned'] for r in earnings_records if r['month'] == '2025-10')
                yesterday_total = sum(r['nos_earned'] for r in earnings_records if r['date'] == yesterday.strftime("%Y-%m-%d"))
                today_total = sum(r['nos_earned'] for r in earnings_records if r['date'] == today.strftime("%Y-%m-%d"))
                
                print(f"      ✅ Added {len(earnings_records)} earnings records")
                print(f"         September: {sept_jobs} jobs, {sept_total:.2f} NOS")
                print(f"         October: {oct_jobs} jobs, {oct_total:.2f} NOS")
                print(f"         Yesterday: {yesterday_jobs} jobs, {yesterday_total:.2f} NOS")
                print(f"         Today: {today_jobs} jobs, {today_total:.2f} NOS")
            
            print()
    
    print("=" * 70)
    print(f"✅ Sample data population complete!")
    print(f"   Total earnings records created: {total_records}")
    print("=" * 70)
    print()
    print("🎉 You can now view earnings statistics in the app!")
    print("   - Node cards will show yesterday's earnings")
    print("   - Click 'View Earnings Statistics' for full breakdown")
    print()


if __name__ == "__main__":
    asyncio.run(populate_sample_data())
