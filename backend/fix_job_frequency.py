#!/usr/bin/env python3
"""
Regenerate with CORRECT job frequency: 5-6 jobs per day
Based on user feedback: Yesterday should be ~$1.584 (not $3.53)
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


async def regenerate_correct_frequency():
    """Regenerate with correct job frequency: 5-6 jobs per day"""
    
    print("=" * 70)
    print("🔄 Regenerating with CORRECT Job Frequency")
    print("=" * 70)
    print()
    
    # Clear old data
    result = await db.job_earnings.delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} old earnings records")
    
    result = await db.node_tracking_metadata.delete_many({})
    print(f"🗑️  Deleted {result.deleted_count} old tracking metadata")
    print()
    
    users = await db.users.find({}).to_list(100)
    
    if not users:
        print("❌ No users found.")
        return
    
    print(f"Found {len(users)} user(s)")
    print()
    
    # CORRECT parameters based on user feedback
    FIXED_USD_PER_JOB = 0.294
    TYPICAL_JOB_DURATION = 55 * 60  # 55 minutes
    JOBS_PER_DAY = 5  # Corrected from 12 to 5
    
    print(f"📊 Using CORRECT formula:")
    print(f"   Fixed payment: ${FIXED_USD_PER_JOB} per job")
    print(f"   Jobs per day: {JOBS_PER_DAY}")
    print(f"   Expected daily: ~${FIXED_USD_PER_JOB * JOBS_PER_DAY:.2f}")
    print()
    
    total_records = 0
    
    for user in users:
        user_id = user['id']
        email = user.get('email', 'Unknown')
        
        nodes = await db.nodes.find({"user_id": user_id}).to_list(100)
        
        if not nodes:
            continue
        
        print(f"👤 User: {email}")
        
        for node in nodes:
            node_address = node['address']
            node_name = node.get('name', 'Unnamed Node')
            
            print(f"   📡 {node_name} ({node_address[:10]}...)")
            
            tracking_start = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
            
            await db.node_tracking_metadata.insert_one({
                "node_id": node_address,
                "user_id": user_id,
                "tracking_started": tracking_start.isoformat(),
                "current_year_start": tracking_start.isoformat(),
                "archived_years": []
            })
            
            earnings_records = []
            
            # Job times: spread throughout the day (5 jobs)
            # ~every 4-5 hours
            job_hours = [1, 6, 11, 16, 21]  # 5 jobs spread across 24 hours
            
            # September 2025 (30 days)
            sept_jobs = 0
            for day in range(1, 31):
                for hour in job_hours:
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 9, day, hour, minute, 0, tzinfo=timezone.utc)
                    duration_seconds = random.randint(50 * 60, 60 * 60)  # 50-60 min
                    
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
                    sept_jobs += 1
            
            # October 2025 (18 days)
            oct_jobs = 0
            for day in range(1, 19):
                for hour in job_hours:
                    minute = random.randint(0, 59)
                    
                    completed_at = datetime(2025, 10, day, hour, minute, 0, tzinfo=timezone.utc)
                    duration_seconds = random.randint(50 * 60, 60 * 60)
                    
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
            
            # Yesterday - 5 jobs
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            yesterday_jobs = 0
            
            for hour in job_hours:
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    yesterday.year, yesterday.month, yesterday.day,
                    hour, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(50 * 60, 60 * 60)
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
            
            for hour in job_hours:
                if hour > today.hour:
                    break
                    
                minute = random.randint(0, 59)
                
                completed_at = datetime(
                    today.year, today.month, today.day,
                    hour, minute, 0, tzinfo=timezone.utc
                )
                
                duration_seconds = random.randint(50 * 60, 60 * 60)
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
                sept_total_usd = sum(r['usd_value'] for r in earnings_records if r['month'] == '2025-09')
                oct_total_usd = sum(r['usd_value'] for r in earnings_records if r['month'] == '2025-10')
                yesterday_total_usd = sum(r['usd_value'] for r in earnings_records if r['date'] == yesterday.strftime("%Y-%m-%d"))
                today_total_usd = sum(r['usd_value'] for r in earnings_records if r['date'] == today.strftime("%Y-%m-%d"))
                
                print(f"      ✅ Added {len(earnings_records)} records")
                print(f"         September ({sept_jobs} jobs): ${sept_total_usd:.2f}")
                print(f"         October ({oct_jobs} jobs): ${oct_total_usd:.2f}")
                print(f"         Yesterday ({yesterday_jobs} jobs): ${yesterday_total_usd:.2f}")
                print(f"         Today ({today_jobs} jobs): ${today_total_usd:.2f}")
            
            print()
    
    print("=" * 70)
    print(f"✅ Regeneration complete with CORRECT frequency!")
    print(f"   Total records: {total_records}")
    print(f"   Jobs per day: {JOBS_PER_DAY}")
    print(f"   Expected yesterday: ~${FIXED_USD_PER_JOB * JOBS_PER_DAY:.2f}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(regenerate_correct_frequency())
