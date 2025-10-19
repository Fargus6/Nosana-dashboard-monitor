#!/usr/bin/env python3
"""
Direct scraping test for node earnings
"""
import asyncio
import sys
sys.path.append('/app/backend')

from datetime import datetime, timezone, timedelta
import os
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

from playwright.async_api import async_playwright
import re

async def scrape_test():
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    
    print(f"\n🌐 Scraping Nosana dashboard for: {node_address}")
    
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
        print("="*80)
        
        # Calculate totals
        total_usd = 0
        job_count = 0
        nos_price = 0.476626
        
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
            
            # Calculate earnings
            duration_hours = duration_seconds / 3600.0
            usd_earned = duration_hours * hourly_rate
            nos_earned = usd_earned / nos_price
            
            print(f"\nJob #{idx}: {job['job_id'][:12]}...")
            print(f"  Started: {job['started']}")
            print(f"  Duration: {duration_text} ({duration_seconds}s = {duration_hours:.4f}h)")
            print(f"  Rate: ${hourly_rate}/h")
            print(f"  Status: {job['status']}")
            print(f"  💰 USD: ${usd_earned:.4f} | NOS: {nos_earned:.2f}")
            
            if job['status'] == 'SUCCESS':
                total_usd += usd_earned
                job_count += 1
        
        total_nos = total_usd / nos_price
        
        print("\n" + "="*80)
        print("📊 TODAY'S SUMMARY (Completed Jobs Only)")
        print("="*80)
        print(f"✅ Jobs Completed: {job_count}")
        print(f"💰 Total USD: ${total_usd:.2f}")
        print(f"💰 Total NOS: {total_nos:.2f} (at ${nos_price}/NOS)")
        print("="*80)

if __name__ == "__main__":
    asyncio.run(scrape_test())
