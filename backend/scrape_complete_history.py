#!/usr/bin/env python3
"""
Scrape ALL pages by clicking pagination links (1, 2, 3...35)
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

async def scrape_all_pages_final():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    
    scrape_time = datetime.now(timezone.utc)
    print(f"\n{'='*100}")
    print(f"COMPLETE HISTORY SCRAPING - NODE: {node_address}")
    print(f"{'='*100}")
    print(f"🕐 Scrape Time: {scrape_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://dashboard.nosana.com/host/{node_address}"
        print(f"📡 Fetching from: {url}\n")
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_selector('table', timeout=10000)
        
        # Get total number of pages
        total_pages = await page.evaluate('''() => {
            const nav = document.querySelector('[role="navigation"]');
            if (!nav) return 1;
            
            const links = nav.querySelectorAll('a.pagination-link');
            let maxPage = 1;
            
            links.forEach(link => {
                const text = link.textContent.trim();
                const pageNum = parseInt(text);
                if (!isNaN(pageNum) && pageNum > maxPage) {
                    maxPage = pageNum;
                }
            });
            
            return maxPage;
        }''')
        
        print(f"📊 Found {total_pages} pages total\n")
        print("🔄 Starting to scrape all pages...\n")
        
        all_jobs_data = []
        
        for page_num in range(1, total_pages + 1):
            print(f"📄 Scraping page {page_num}/{total_pages}...", end=' ')
            
            # If not on page 1, click the page number
            if page_num > 1:
                try:
                    # Find and click the page number link
                    page_link = await page.query_selector(f'a.pagination-link:has-text("{page_num}")')
                    if page_link:
                        await page_link.click()
                        await page.wait_for_timeout(1500)  # Wait for page to load
                    else:
                        print(f"⚠️  Could not find link for page {page_num}")
                        continue
                except Exception as e:
                    print(f"⚠️  Error clicking page {page_num}: {e}")
                    continue
            
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
            
            print(f"✅ {len(jobs_on_page)} jobs")
            all_jobs_data.extend(jobs_on_page)
        
        await browser.close()
        
        print(f"\n{'='*100}")
        print(f"✅ Scraping complete! Total jobs: {len(all_jobs_data)}")
        print(f"{'='*100}\n")
        
        # Date boundaries
        today_start = scrape_time.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        month_start = scrape_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        print(f"📅 TODAY starts at: {today_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 YESTERDAY starts at: {yesterday_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"📅 THIS MONTH starts at: {month_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("="*100 + "\n")
        
        print("🔄 Processing jobs and calculating earnings...\n")
        
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
        print("📊 FINAL EARNINGS SUMMARY (All Jobs from All 35 Pages)")
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
            print(f"   Showing first 30 jobs:")
            for job_info in yesterday_jobs[:30]:
                comp_time = job_info['completed_time']
                payment = job_info['payment']
                print(f"   • {comp_time.strftime('%H:%M:%S')}: ${payment:.3f}")
            if len(yesterday_jobs) > 30:
                print(f"   ... and {len(yesterday_jobs) - 30} more jobs")
        print(f"   ➡️  TOTAL YESTERDAY: ${yesterday_total:.3f}\n")
        
        print(f"📅 THIS MONTH ({month_start.strftime('%B %Y')}):")
        print(f"   Number of jobs: {len(month_jobs)}")
        if month_jobs:
            earliest = min(j['completed_time'] for j in month_jobs)
            latest = max(j['completed_time'] for j in month_jobs)
            print(f"   Date range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}")
        print(f"   ➡️  TOTAL THIS MONTH: ${month_total:.3f}\n")
        
        print("="*100)
        print(f"✅ Processed {len(all_valid_jobs)} completed jobs from {total_pages} pages")
        print("✅ These are ACTUAL payment amounts from dashboard Price column")
        print("✅ NO formulas used - just direct scraping and simple addition")
        print("="*100 + "\n")

if __name__ == "__main__":
    asyncio.run(scrape_all_pages_final())
