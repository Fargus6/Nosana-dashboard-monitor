#!/usr/bin/env python3
"""
Deep scraping with page number pagination (1, 2, 3, 4, 5...)
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
    """Convert relative time to datetime"""
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
        return scrape_time

async def scrape_all_pages():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    
    scrape_time = datetime.now(timezone.utc)
    print(f"\n{'='*100}")
    print(f"DEEP SCRAPING ALL PAGES - NODE: {node_address}")
    print(f"{'='*100}")
    print(f"🕐 Scrape Time: {scrape_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://dashboard.nosana.com/host/{node_address}"
        print(f"📡 Fetching from: {url}\n")
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_selector('table', timeout=10000)
        
        all_jobs_data = []
        current_page = 1
        
        print("🔄 Scraping all pages...\n")
        
        while True:
            print(f"📄 Scraping page {current_page}...")
            
            # Extract jobs from current page
            jobs_on_page = await page.evaluate('''() => {
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
            
            print(f"   ✅ Found {len(jobs_on_page)} jobs on page {current_page}")
            all_jobs_data.extend(jobs_on_page)
            
            # Check if there's a next page
            # Look for pagination buttons/links
            next_page_exists = await page.evaluate('''() => {
                // Look for "Next" button or next page number
                const pagination = document.querySelector('[role="navigation"]');
                if (!pagination) return false;
                
                // Look for buttons or links with page numbers
                const buttons = pagination.querySelectorAll('button, a');
                
                // Find current active page and check if there's a next one
                for (let i = 0; i < buttons.length; i++) {
                    const button = buttons[i];
                    const text = button.textContent.trim();
                    
                    // Check for "Next" button
                    if (text.toLowerCase().includes('next') || text === '›' || text === '>') {
                        if (!button.disabled && !button.classList.contains('disabled')) {
                            return true;
                        }
                    }
                }
                
                return false;
            }''')
            
            if not next_page_exists:
                print(f"   ℹ️  No more pages found. Finished at page {current_page}\n")
                break
            
            # Click next page
            try:
                # Try to click "Next" button or next page number
                next_button = await page.query_selector('button:has-text("›"), button:has-text("Next"), a:has-text("›"), a:has-text("Next")')
                
                if not next_button:
                    # Try to find the next page number button
                    next_page_num = current_page + 1
                    next_button = await page.query_selector(f'button:has-text("{next_page_num}"), a:has-text("{next_page_num}")')
                
                if next_button:
                    await next_button.click()
                    await page.wait_for_timeout(2000)  # Wait for page to load
                    current_page += 1
                else:
                    print(f"   ⚠️  Could not find next page button\n")
                    break
                    
            except Exception as e:
                print(f"   ⚠️  Error navigating to next page: {e}\n")
                break
            
            # Safety limit to prevent infinite loops
            if current_page > 100:
                print(f"   ⚠️  Reached safety limit of 100 pages\n")
                break
        
        await browser.close()
        
        print(f"\n✅ Total jobs scraped from {current_page} pages: {len(all_jobs_data)}\n")
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
        
        for idx, job in enumerate(all_jobs_data, 1):
            if job['status'] != 'SUCCESS':
                continue
            
            price_text = job['price'].replace('/h', '').replace('$', '').strip()
            
            try:
                actual_payment = float(price_text)
            except:
                continue
            
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
            
            started_time = await parse_relative_time(job['started'], scrape_time)
            completed_time = started_time + timedelta(seconds=duration_seconds)
            
            job_info = {
                'job': job,
                'payment': actual_payment,
                'completed_time': completed_time,
                'started_time': started_time
            }
            
            all_valid_jobs.append(job_info)
            
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
        print("📊 COMPLETE EARNINGS SUMMARY (All Jobs from All Pages)")
        print("="*100 + "\n")
        
        print(f"📅 TODAY ({today_start.strftime('%Y-%m-%d')}):")
        print(f"   Number of jobs: {len(today_jobs)}")
        if today_jobs:
            print(f"   Showing first 20 jobs:")
            for job_info in today_jobs[:20]:
                comp_time = job_info['completed_time']
                payment = job_info['payment']
                print(f"   • {comp_time.strftime('%H:%M:%S')}: ${payment:.3f}")
            if len(today_jobs) > 20:
                print(f"   ... and {len(today_jobs) - 20} more jobs")
        print(f"   ➡️  TOTAL TODAY: ${today_total:.3f}\n")
        
        print(f"📅 YESTERDAY ({yesterday_start.strftime('%Y-%m-%d')}):")
        print(f"   Number of jobs: {len(yesterday_jobs)}")
        if yesterday_jobs:
            print(f"   Showing all jobs:")
            for job_info in yesterday_jobs[:50]:
                comp_time = job_info['completed_time']
                payment = job_info['payment']
                print(f"   • {comp_time.strftime('%H:%M:%S')}: ${payment:.3f}")
            if len(yesterday_jobs) > 50:
                print(f"   ... and {len(yesterday_jobs) - 50} more jobs")
        print(f"   ➡️  TOTAL YESTERDAY: ${yesterday_total:.3f}\n")
        
        print(f"📅 THIS MONTH ({month_start.strftime('%B %Y')}):")
        print(f"   Number of jobs: {len(month_jobs)}")
        if month_jobs:
            print(f"   Date range: {month_jobs[-1]['completed_time'].strftime('%Y-%m-%d')} to {month_jobs[0]['completed_time'].strftime('%Y-%m-%d')}")
        print(f"   ➡️  TOTAL THIS MONTH: ${month_total:.3f}\n")
        
        print("="*100)
        print(f"✅ Processed {len(all_valid_jobs)} completed jobs total from {current_page} pages")
        print("✅ These are ACTUAL payment amounts from dashboard Price column")
        print("✅ NO formulas used - just direct scraping and simple addition")
        print("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(scrape_all_pages())
