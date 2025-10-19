#!/usr/bin/env python3
"""
Generate CORRECT sample data:
- RTX 3090: $0.176/hr
- ~12 jobs per day (varies 10-14 to be realistic)
- ~55-60 minute jobs
- Daily earnings: ~$2.11 for 3090
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.getenv('DB_NAME', 'test_database')

db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client[DB_NAME]


async def generate_realistic_data():
    """Generate realistic earnings with varying job counts"""
    
    print("=" * 70)
    print("🎯 Generating REALISTIC Earnings Data")
    print("=" * 70)
    print()
    
    # Clear old data
    result = await db.job_earnings.delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} old records")
    
    result = await db.node_tracking_metadata.delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} old metadata")
    print()
    
    users = await db.users.find({}).to_list(100)
    
    if not users:
        print("❌ No users found")
        return
    
    print(f"👥 Found {len(users)} users")
    print()
    print("📊 Formula: (hourly_rate × duration_hours) / nos_price")
    print("💰 RTX 3090: $0.176/hr")
    print("⏱️  Job duration: 55-60 minutes")
    print("🔄 Jobs per day: 10-14 (varies realistically)")
    print()
    
    total_records = 0
    
    for user in users:
        user_id = user['id']
        email = user.get('email', 'Unknown')
        
        nodes = await db.nodes.find({"user_id": user_id}).to_list(100)
        
        if not nodes:
            continue
        
        print(f"👤 {email}")
        
        for node in nodes:
            node_address = node['address']
            node_name = node.get('name', 'Unnamed')
            
            # Set GPU type to 3090 for all nodes
            await db.nodes.update_one(
                {"address": node_address, "user_id": user_id},
                {"$set": {"gpu_type": "3090"}}
            )
            
            print(f"   📡 {node_name[:20]} (RTX 3090)")
            
            # Create tracking metadata
            tracking_start = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
            
            await db.node_tracking_metadata.insert_one({
                "node_id": node_address,
                "user_id": user_id,
                "tracking_started": tracking_start.isoformat(),
                "current_year_start": tracking_start.isoformat(),
                "archived_years": []
            })
            
            earnings_records = []
            
            # September (30 days)
            sept_jobs = 0
            for day in range(1, 31):
                # Vary jobs per day: 10-14 jobs
                jobs_today = random.randint(10, 14)
                
                # Distribute jobs throughout the day
                for job_num in range(jobs_today):
                    # Spread evenly: 24 hours / jobs_today
                    hour_spacing = 24.0 / jobs_today
                    hour = int(job_num * hour_spacing) + random.randint(-1, 1)
                    hour = max(0, min(23, hour))  # Keep in valid range
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 9, day, hour, minute, 0, tzinfo=timezone.utc)
                    
                    # Duration: 55-60 minutes
                    duration_seconds = random.randint(55 * 60, 60 * 60)
                    
                    # Calculate payment: RTX 3090 rate
                    hourly_rate = 0.176
                    duration_hours = duration_seconds / 3600.0
                    usd_earned = hourly_rate * duration_hours
                    
                    # NOS price
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
            
            # October (18 days)
            oct_jobs = 0
            for day in range(1, 19):
                jobs_today = random.randint(10, 14)
                
                for job_num in range(jobs_today):
                    hour_spacing = 24.0 / jobs_today
                    hour = int(job_num * hour_spacing) + random.randint(-1, 1)
                    hour = max(0, min(23, hour))
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 10, day, hour, minute, 0, tzinfo=timezone.utc)
                    duration_seconds = random.randint(55 * 60, 60 * 60)
                    
                    hourly_rate = 0.176
                    duration_hours = duration_seconds / 3600.0
                    usd_earned = hourly_rate * duration_hours
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
            yesterday_jobs = 12
            
            for job_num in range(yesterday_jobs):
                hour_spacing = 24.0 / yesterday_jobs
                hour = int(job_num * hour_spacing)
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    yesterday.year, yesterday.month, yesterday.day,
                    hour, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(55 * 60, 60 * 60)
                hourly_rate = 0.176
                duration_hours = duration_seconds / 3600.0
                usd_earned = hourly_rate * duration_hours
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
            
            # Today - jobs so far
            today = datetime.now(timezone.utc)
            today_jobs = 0
            jobs_today_total = 12
            
            for job_num in range(jobs_today_total):
                hour_spacing = 24.0 / jobs_today_total
                hour = int(job_num * hour_spacing)
                
                if hour > today.hour:
                    break
                    
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    today.year, today.month, today.day,
                    hour, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(55 * 60, 60 * 60)
                hourly_rate = 0.176
                duration_hours = duration_seconds / 3600.0
                usd_earned = hourly_rate * duration_hours
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
            
            # Insert records
            if earnings_records:
                await db.job_earnings.insert_many(earnings_records)
                total_records += len(earnings_records)
                
                # Calculate totals
                yesterday_total = sum(r['usd_value'] for r in earnings_records if r['date'] == yesterday.strftime("%Y-%m-%d"))
                sept_total = sum(r['usd_value'] for r in earnings_records if r['month'] == '2025-09')
                oct_total = sum(r['usd_value'] for r in earnings_records if r['month'] == '2025-10')
                
                print(f"      ✅ Generated {len(earnings_records)} records")
                print(f"         Yesterday ({yesterday_jobs} jobs): ${yesterday_total:.2f}")
                print(f"         September ({sept_jobs} jobs): ${sept_total:.2f}")
                print(f"         October ({oct_jobs} jobs): ${oct_total:.2f}")
            
            print()
    
    print("=" * 70)
    print(f"✅ Generated {total_records} realistic earnings records")
    print(f"💰 RTX 3090: $0.176/hr × ~1hr = ~$0.176/job")
    print(f"📊 12 jobs/day × $0.176 = ~$2.11/day")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(generate_realistic_data())
