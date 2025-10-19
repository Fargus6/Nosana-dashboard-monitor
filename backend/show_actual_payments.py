#!/usr/bin/env python3
"""
Show actual payment amounts from Nosana dashboard price column
"""
import asyncio
import sys
sys.path.append('/app/backend')

from datetime import datetime, timezone, timedelta
import os
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

from playwright.async_api import async_playwright
import re

async def parse_relative_time(time_text: str, scrape_time: datetime) -> datetime:
    """Convert relative time like '3 hours ago' to datetime"""
    try:
        hours_match = re.search(r'(\d+)\s+hours?\s+ago', time_text)
        if hours_match:
            return scrape_time - timedelta(hours=int(hours_match.group(1)))
        
        minutes_match = re.search(r'(\d+)\s+minutes?\s+ago', time_text)
        if minutes_match:
            return scrape_time - timedelta(minutes=int(minutes_match.group(1)))
        
        days_match = re.search(r'(\d+)\s+days?\s+ago', time_text)
        if days_match:
            return scrape_time - timedelta(days=int(days_match.group(1)))
        
        return scrape_time
    except Exception as e:
        print(f"Error parsing relative time '{time_text}': {str(e)}")
        return scrape_time

async def show_actual_earnings():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    
    scrape_time = datetime.now(timezone.utc)
    print(f"\n{'='*100}")
    print(f"ACTUAL EARNINGS FROM DASHBOARD - NODE: {node_address}")
    print(f"{'='*100}")
    print(f"🕐 Scrape Time: {scrape_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        url = f"https://dashboard.nosana.com/host/{node_address}"
        print(f"📡 Fetching from: {url}\n")
        
        await page.goto(url, wait_until='networkidle', timeout=15000)
        await page.wait_for_selector('table', timeout=10000)
        
        # Extract jobs with ACTUAL PRICE from dashboard
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
                    
                    // Get the actual price from the price column (column 4)
                    const priceText = cells[4].textContent.trim();
                    
                    jobs.push({
                        job_id: jobId,
                        started: cells[2].textContent.trim(),
                        duration: cells[3].textContent.trim(),
                        price: priceText,  // This is the ACTUAL payment amount
                        gpu: cells[5].textContent.trim(),
                        status: cells[6].textContent.trim().includes('RUNNING') ? 'RUNNING' : 'SUCCESS'
                    });
                }
            }
            
            return jobs;
        }''')
        
        await browser.close()
        
        print(f"✅ Found {len(jobs_data)} jobs on dashboard\n")
        print("="*100)
        
        # Date boundaries
        today_start = scrape_time.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        month_start = scrape_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        print(f"📅 TODAY starts at: {today_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 YESTERDAY was: {yesterday_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 THIS MONTH starts at: {month_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("="*100 + "\n")
        
        today_jobs = []
        yesterday_jobs = []
        month_jobs = []
        
        for idx, job in enumerate(jobs_data, 1):
            if job['status'] != 'SUCCESS':
                continue
            
            # Parse the ACTUAL payment amount from price column
            # The price column shows the actual payment like "$0.176" or "$0.176/h"
            price_text = job['price'].replace('/h', '').replace('$', '').strip()
            
            try:
                actual_payment = float(price_text)
            except:
                print(f"⚠️  Could not parse price: {job['price']}")
                continue
            
            # Parse duration to get completed time
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
            
            # Calculate started and completed times
            started_time = await parse_relative_time(job['started'], scrape_time)
            completed_time = started_time + timedelta(seconds=duration_seconds)
            
            # Categorize by date
            day_label = "OLDER"
            if completed_time >= today_start:
                day_label = "TODAY"
                today_jobs.append((job, actual_payment, completed_time))
            elif completed_time >= yesterday_start:
                day_label = "YESTERDAY"
                yesterday_jobs.append((job, actual_payment, completed_time))
            
            if completed_time >= month_start:
                month_jobs.append((job, actual_payment, completed_time))
            
            print(f"Job #{idx}: {job['job_id'][:12]}...")
            print(f"  Started: {job['started']} → {started_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Completed: {completed_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Duration: {duration_text}")
            print(f"  💰 ACTUAL PAYMENT FROM DASHBOARD: ${actual_payment}")
            print(f"  📅 DAY: {day_label}\n")
        
        # Calculate totals by simple addition
        today_total = sum(payment for _, payment, _ in today_jobs)
        yesterday_total = sum(payment for _, payment, _ in yesterday_jobs)
        month_total = sum(payment for _, payment, _ in month_jobs)
        
        print("\n" + "="*100)
        print("📊 EARNINGS SUMMARY (Based on Actual Dashboard Price Column)")
        print("="*100 + "\n")
        
        print(f"📅 TODAY ({today_start.strftime('%Y-%m-%d')}):")
        print(f"   Number of jobs: {len(today_jobs)}")
        if today_jobs:
            for job, payment, comp_time in today_jobs:
                print(f"   • {comp_time.strftime('%H:%M:%S')}: ${payment:.3f}")
        print(f"   ➡️  TOTAL TODAY: ${today_total:.3f}\n")
        
        print(f"📅 YESTERDAY ({yesterday_start.strftime('%Y-%m-%d')}):")
        print(f"   Number of jobs: {len(yesterday_jobs)}")
        if yesterday_jobs:
            for job, payment, comp_time in yesterday_jobs:
                print(f"   • {comp_time.strftime('%H:%M:%S')}: ${payment:.3f}")
        print(f"   ➡️  TOTAL YESTERDAY: ${yesterday_total:.3f}\n")
        
        print(f"📅 THIS MONTH ({month_start.strftime('%B %Y')}):")
        print(f"   Number of jobs: {len(month_jobs)}")
        print(f"   ➡️  TOTAL THIS MONTH: ${month_total:.3f}\n")
        
        print("="*100)
        print("✅ These are ACTUAL payment amounts from dashboard Price column")
        print("✅ NO formulas used - just direct scraping and simple addition")
        print("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(show_actual_earnings())
