#!/usr/bin/env python3
"""
Test script for scraping Nosana dashboard using Playwright for dynamic content
"""
import asyncio
import os
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

from playwright.async_api import async_playwright
import re
import json

async def scrape_nosana_with_playwright(node_address: str):
    """Scrape Nosana dashboard using Playwright for dynamic content"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            url = f"https://dashboard.nosana.com/host/{node_address}"
            print(f"\n🌐 Loading Nosana dashboard: {url}")
            
            # Navigate to page
            await page.goto(url, wait_until='networkidle')
            
            # Wait for table to load
            await page.wait_for_selector('table', timeout=10000)
            
            print("✅ Page loaded, extracting job data...")
            
            # Extract job data from table
            jobs = await page.evaluate('''() => {
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
            
            print(f"\n📊 Found {len(jobs)} jobs:\n")
            
            for i, job in enumerate(jobs[:10], 1):  # Show first 10
                duration_seconds = parse_duration_to_seconds(job['duration'])
                hourly_rate = parse_hourly_rate(job['price'])
                usd_earned = (duration_seconds / 3600.0) * hourly_rate
                
                print(f"Job #{i}: {job['job_id'][:12] if job['job_id'] else 'N/A'}...")
                print(f"  Started: {job['started']}")
                print(f"  Duration: {job['duration']} ({duration_seconds}s)")
                print(f"  Rate: {job['price']} (${hourly_rate}/h)")
                print(f"  GPU: {job['gpu']}")
                print(f"  Status: {job['status']}")
                print(f"  💰 Earnings: ${usd_earned:.4f}")
                print()
            
            # Calculate totals
            total_usd = 0
            for job in jobs:
                if job['status'] == 'SUCCESS':
                    duration_seconds = parse_duration_to_seconds(job['duration'])
                    hourly_rate = parse_hourly_rate(job['price'])
                    total_usd += (duration_seconds / 3600.0) * hourly_rate
            
            print(f"\n✅ Successfully scraped {len(jobs)} jobs")
            print(f"💰 Total Earnings (completed): ${total_usd:.2f}")
            
            await browser.close()
            return jobs
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await browser.close()
            return []


def parse_duration_to_seconds(duration_text: str) -> int:
    """Convert duration text like '55m 9s' or '1h 23m' to seconds"""
    try:
        seconds = 0
        hours_match = re.search(r'(\d+)h', duration_text)
        if hours_match:
            seconds += int(hours_match.group(1)) * 3600
        
        minutes_match = re.search(r'(\d+)m', duration_text)
        if minutes_match:
            seconds += int(minutes_match.group(1)) * 60
        
        seconds_match = re.search(r'(\d+)s', duration_text)
        if seconds_match:
            seconds += int(seconds_match.group(1))
        
        return seconds
    except Exception as e:
        return 0


def parse_hourly_rate(price_text: str) -> float:
    """Extract hourly rate from price text like '$0.176' or '$0.192/h'"""
    try:
        rate_str = price_text.replace('/h', '').replace('$', '').strip()
        return float(rate_str)
    except Exception as e:
        return 0.0


if __name__ == "__main__":
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    asyncio.run(scrape_nosana_with_playwright(node_address))
