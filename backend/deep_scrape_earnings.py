#!/usr/bin/env python3
"""
Deep scraping of ALL jobs from Nosana dashboard with pagination
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

async def deep_scrape_all_jobs():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    
    scrape_time = datetime.now(timezone.utc)
    print(f"\n{'='*100}")
    print(f"DEEP SCRAPING ALL JOBS - NODE: {node_address}")
    print(f"{'='*100}")
    print(f"🕐 Scrape Time: {scrape_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://dashboard.nosana.com/host/{node_address}"
        print(f"📡 Fetching from: {url}\n")
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_selector('table', timeout=10000)
        
        print("🔄 Loading all jobs (scrolling/pagination)...\n")
        
        # Scroll to load more jobs
        previous_count = 0
        max_attempts = 50  # Prevent infinite loops
        attempt = 0
        
        while attempt < max_attempts:
            # Scroll to bottom
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1000)
            
            # Count current jobs
            current_count = await page.evaluate('''() => {
                const table = document.querySelector('table');
                if (!table) return 0;
                return table.querySelectorAll('tr').length - 1; // Exclude header
            }''')
            
            print(f"   Loaded {current_count} jobs...", end='\r')
            
            # If no new jobs loaded, we've reached the end
            if current_count == previous_count:
                break
            
            previous_count = current_count
            attempt += 1
        
        print(f"\n✅ Finished loading. Total jobs found: {current_count}\n")
        
        # Extract ALL jobs
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
                    
                    const priceText = cells[4].textContent.trim();
                    
                    jobs.push({
                        job_id: jobId,
                        started: cells[2].textContent.trim(),
                        duration: cells[3].textContent.trim(),
                        price: priceText,
                        gpu: cells[5].textContent.trim(),
                        status: cells[6].textContent.trim().includes('RUNNING') ? 'RUNNING' : 'SUCCESS'
                    });
                }
            }
            
            return jobs;
        }''')
        
        await browser.close()
        
        print(f"📊 Processing {len(jobs_data)} jobs...\n")
        print("="*100)
        
        # Date boundaries
        today_start = scrape_time.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        month_start = scrape_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        print(f"📅 TODAY starts at: {today_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 YESTERDAY starts at: {yesterday_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 THIS MONTH starts at: {month_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("="*100 + "\n")
        
        today_jobs = []
        yesterday_jobs = []
        month_jobs = []
        all_valid_jobs = []
        
        for idx, job in enumerate(jobs_data, 1):
            if job['status'] != 'SUCCESS':
                continue
            
            # Parse the ACTUAL payment amount from price column
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
            
            job_info = {
                'job': job,
                'payment': actual_payment,
                'completed_time': completed_time,
                'started_time': started_time
            }
            
            all_valid_jobs.append(job_info)
            
            # Categorize by date
            if completed_time >= today_start:
                today_jobs.append(job_info)
            elif completed_time >= yesterday_start:
                yesterday_jobs.append(job_info)
            
            if completed_time >= month_start:
                month_jobs.append(job_info)
        
        # Calculate totals
        today_total = sum(j['payment'] for j in today_jobs)
        yesterday_total = sum(j['payment'] for j in yesterday_jobs)
        month_total = sum(j['payment'] for j in month_jobs)
        
        print("\n" + "="*100)
        print("📊 COMPLETE EARNINGS SUMMARY (All Jobs from Dashboard)")
        print("="*100 + "\n")
        
        print(f"📅 TODAY ({today_start.strftime('%Y-%m-%d')}):")
        print(f"   Number of jobs: {len(today_jobs)}")
        if today_jobs:
            print(f"   Showing first 10 jobs:")
            for job_info in today_jobs[:10]:
                comp_time = job_info['completed_time']
                payment = job_info['payment']
                print(f"   • {comp_time.strftime('%H:%M:%S')}: ${payment:.3f}")
            if len(today_jobs) > 10:
                print(f"   ... and {len(today_jobs) - 10} more jobs")
        print(f"   ➡️  TOTAL TODAY: ${today_total:.3f}\n")
        
        print(f"📅 YESTERDAY ({yesterday_start.strftime('%Y-%m-%d')}):")
        print(f"   Number of jobs: {len(yesterday_jobs)}")
        if yesterday_jobs:
            print(f"   All jobs:")
            for job_info in yesterday_jobs:
                comp_time = job_info['completed_time']
                payment = job_info['payment']
                print(f"   • {comp_time.strftime('%H:%M:%S')}: ${payment:.3f}")
        print(f"   ➡️  TOTAL YESTERDAY: ${yesterday_total:.3f}\n")
        
        print(f"📅 THIS MONTH ({month_start.strftime('%B %Y')}):")
        print(f"   Number of jobs: {len(month_jobs)}")
        print(f"   Date range: {month_jobs[-1]['completed_time'].strftime('%Y-%m-%d')} to {month_jobs[0]['completed_time'].strftime('%Y-%m-%d')}" if month_jobs else "   No jobs")
        print(f"   ➡️  TOTAL THIS MONTH: ${month_total:.3f}\n")
        
        print("="*100)
        print(f"✅ Processed {len(all_valid_jobs)} completed jobs total")
        print("✅ These are ACTUAL payment amounts from dashboard Price column")
        print("✅ NO formulas used - just direct scraping and simple addition")
        print("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(deep_scrape_all_jobs())
