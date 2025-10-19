#!/usr/bin/env python3
"""
CLEAR old sample data and regenerate with REALISTIC earnings
Based on actual Nosana dashboard data:
- Fixed payment: $0.294 per job (regardless of duration)
- Job duration: ~55 minutes consistently
- Frequency: ~12 jobs per day (1 every 2 hours)
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


async def clear_and_regenerate():
    """Clear old data and regenerate with realistic earnings"""
    
    print("=" * 70)
    print("🔄 Clearing Old Sample Data & Regenerating with REAL Formula")
    print("=" * 70)
    print()
    
    # Clear old earnings data
    result = await db.job_earnings.delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} old earnings records")
    
    result = await db.node_tracking_metadata.delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} old tracking metadata")
    print()
    
    # Get all users and their nodes
    users = await db.users.find({}).to_list(100)
    
    if not users:
        print("❌ No users found.")
        return
    
    print(f"Found {len(users)} user(s)")
    print()
    
    # REAL Nosana payment formula
    FIXED_USD_PER_JOB = 0.294  # Fixed payment per job
    TYPICAL_JOB_DURATION = 55 * 60  # 55 minutes in seconds
    JOBS_PER_DAY = 12  # About 1 every 2 hours
    
    total_records = 0
    
    for user in users:
        user_id = user['id']
        email = user.get('email', 'Unknown')
        
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
            
            # Create tracking metadata (started Sept 1)
            tracking_start = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
            
            await db.node_tracking_metadata.insert_one({
                "node_id": node_address,
                "user_id": user_id,
                "tracking_started": tracking_start.isoformat(),
                "current_year_start": tracking_start.isoformat(),
                "archived_years": []
            })
            
            print(f"      ✅ Created tracking metadata (started: Sept 1, 2025)")
            
            earnings_records = []
            
            # September 2025 (Sept 1-30) - 30 days
            sept_jobs = 0
            for day in range(1, 31):
                # 12 jobs per day, evenly spaced (~every 2 hours)
                for hour_offset in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 9, day, hour_offset, minute, 0, tzinfo=timezone.utc)
                    
                    # Duration: 55 minutes ± 2 minutes
                    duration_seconds = random.randint(53 * 60, 57 * 60)
                    
                    # Fixed USD payment
                    usd_earned = FIXED_USD_PER_JOB
                    
                    # NOS price varies slightly around $0.46
                    nos_price = random.uniform(0.44, 0.48)
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
            
            # October 2025 (Oct 1-18) - 18 days so far
            oct_jobs = 0
            for day in range(1, 19):
                for hour_offset in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 10, day, hour_offset, minute, 0, tzinfo=timezone.utc)
                    
                    duration_seconds = random.randint(53 * 60, 57 * 60)
                    usd_earned = FIXED_USD_PER_JOB
                    nos_price = random.uniform(0.44, 0.48)
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
            
            # Yesterday - 12 jobs
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            yesterday_jobs = 0
            
            for hour_offset in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    yesterday.year, yesterday.month, yesterday.day,
                    hour_offset, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(53 * 60, 57 * 60)
                usd_earned = FIXED_USD_PER_JOB
                nos_price = random.uniform(0.44, 0.48)
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
            
            # Today - some jobs so far
            today = datetime.now(timezone.utc)
            today_jobs = 0
            current_hour = today.hour
            
            for hour_offset in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
                if hour_offset > current_hour:
                    break
                    
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    today.year, today.month, today.day,
                    hour_offset, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(53 * 60, 57 * 60)
                usd_earned = FIXED_USD_PER_JOB
                nos_price = random.uniform(0.44, 0.48)
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
            
            # Insert all records
            if earnings_records:
                await db.job_earnings.insert_many(earnings_records)
                total_records += len(earnings_records)
                
                # Calculate totals
                sept_total_nos = sum(r['nos_earned'] for r in earnings_records if r['month'] == '2025-09')
                sept_total_usd = sum(r['usd_value'] for r in earnings_records if r['month'] == '2025-09')
                
                oct_total_nos = sum(r['nos_earned'] for r in earnings_records if r['month'] == '2025-10')
                oct_total_usd = sum(r['usd_value'] for r in earnings_records if r['month'] == '2025-10')
                
                yesterday_total_nos = sum(r['nos_earned'] for r in earnings_records if r['date'] == yesterday.strftime("%Y-%m-%d"))
                yesterday_total_usd = sum(r['usd_value'] for r in earnings_records if r['date'] == yesterday.strftime("%Y-%m-%d"))
                
                today_total_nos = sum(r['nos_earned'] for r in earnings_records if r['date'] == today.strftime("%Y-%m-%d"))
                today_total_usd = sum(r['usd_value'] for r in earnings_records if r['date'] == today.strftime("%Y-%m-%d"))
                
                print(f"      ✅ Added {len(earnings_records)} realistic earnings records")
                print(f"      📊 REAL FORMULA: Fixed $0.294 per job")
                print(f"         September ({sept_jobs} jobs): {sept_total_nos:.2f} NOS (${sept_total_usd:.2f})")
                print(f"         October ({oct_jobs} jobs): {oct_total_nos:.2f} NOS (${oct_total_usd:.2f})")
                print(f"         Yesterday ({yesterday_jobs} jobs): {yesterday_total_nos:.2f} NOS (${yesterday_total_usd:.2f})")
                print(f"         Today ({today_jobs} jobs): {today_total_nos:.2f} NOS (${today_total_usd:.2f})")
            
            print()
    
    print("=" * 70)
    print(f"✅ Realistic data regeneration complete!")
    print(f"   Total earnings records created: {total_records}")
    print(f"   Formula: Fixed $0.294 USD per job")
    print(f"   Jobs per day: ~12 (every 2 hours)")
    print(f"   Duration: ~55 minutes per job")
    print("=" * 70)
    print()
    print("🎉 Refresh the app to see REALISTIC earnings!")
    print()


if __name__ == "__main__":
    asyncio.run(clear_and_regenerate())
