#!/usr/bin/env python3
"""
Test timezone-aware scraping
"""
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import sys
sys.path.append('/app/backend')

async def test_timezone():
    user_timezone = "Europe/Helsinki"  # UTC+3
    
    # Get current time in user's timezone
    user_tz = ZoneInfo(user_timezone)
    now_user_tz = datetime.now(user_tz)
    
    print(f"\n🕐 Current time in {user_timezone}: {now_user_tz.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Calculate today's boundaries in user's timezone
    today_start_user_tz = now_user_tz.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start_user_tz = today_start_user_tz - timedelta(days=1)
    
    print(f"📅 Today started at: {today_start_user_tz.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"📅 Yesterday was: {yesterday_start_user_tz.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Test with job times
    print("\n" + "="*80)
    print("JOB CLASSIFICATION TEST:")
    print("="*80)
    
    job_times = [
        ("3 hours ago", 3),
        ("5 hours ago", 5),
        ("7 hours ago", 7),
        ("9 hours ago", 9),
        ("11 hours ago", 11),
        ("13 hours ago", 13),
        ("15 hours ago", 15),
        ("17 hours ago", 17),
        ("19 hours ago", 19),
    ]
    
    today_count = 0
    yesterday_count = 0
    
    for job_text, hours_ago in job_times:
        # Calculate when job completed
        completed_time = now_user_tz - timedelta(hours=hours_ago)
        
        # Check which day
        if completed_time >= today_start_user_tz:
            day = "TODAY"
            today_count += 1
        elif completed_time >= yesterday_start_user_tz:
            day = "YESTERDAY"
            yesterday_count += 1
        else:
            day = "OLDER"
        
        print(f"{job_text:15} → {completed_time.strftime('%Y-%m-%d %H:%M')} → {day}")
    
    print("\n" + "="*80)
    print(f"✅ TODAY: {today_count} jobs")
    print(f"✅ YESTERDAY: {yesterday_count} jobs")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_timezone())
