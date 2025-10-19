#!/usr/bin/env python3
"""
Test script for scraping Nosana dashboard
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta

def parse_duration_to_seconds(duration_text: str) -> int:
    """Convert duration text like '55m 9s' or '1h 23m' to seconds"""
    try:
        seconds = 0
        # Match hours
        hours_match = re.search(r'(\d+)h', duration_text)
        if hours_match:
            seconds += int(hours_match.group(1)) * 3600
        
        # Match minutes
        minutes_match = re.search(r'(\d+)m', duration_text)
        if minutes_match:
            seconds += int(minutes_match.group(1)) * 60
        
        # Match seconds
        seconds_match = re.search(r'(\d+)s', duration_text)
        if seconds_match:
            seconds += int(seconds_match.group(1))
        
        return seconds
    except Exception as e:
        print(f"Error parsing duration '{duration_text}': {str(e)}")
        return 0


def parse_hourly_rate(price_text: str) -> float:
    """Extract hourly rate from price text like '$0.176' or '$0.192/h'"""
    try:
        # Remove '/h' suffix and '$' prefix
        rate_str = price_text.replace('/h', '').replace('$', '').strip()
        return float(rate_str)
    except Exception as e:
        print(f"Error parsing hourly rate '{price_text}': {str(e)}")
        return 0.0


def scrape_nosana_job_history(node_address: str):
    """Scrape actual job history data from Nosana dashboard"""
    try:
        url = f"https://dashboard.nosana.com/host/{node_address}"
        print(f"\n🌐 Scraping Nosana dashboard: {url}")
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to fetch dashboard: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []
        
        # Find the deployments table
        table = soup.find('table')
        if not table:
            print("❌ No jobs table found on dashboard")
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header row
        print(f"📊 Found {len(rows)} job rows\n")
        
        for i, row in enumerate(rows, 1):
            try:
                cols = row.find_all('td')
                if len(cols) < 6:
                    continue
                
                # Extract job data
                job_link = cols[0].find('a')
                job_id = job_link['href'].split('/')[-1] if job_link else None
                
                # Parse started time
                started_text = cols[2].get_text(strip=True)
                
                # Parse duration (e.g., "55m 9s" or "1h 23m")
                duration_text = cols[3].get_text(strip=True)
                duration_seconds = parse_duration_to_seconds(duration_text)
                duration_hours = duration_seconds / 3600.0
                
                # Parse price (e.g., "$0.176" or "$0.192/h")
                price_text = cols[4].get_text(strip=True)
                hourly_rate = parse_hourly_rate(price_text)
                
                # GPU type
                gpu_text = cols[5].get_text(strip=True)
                
                # Status
                status_html = str(cols[6])
                status = "RUNNING" if "running" in status_html else "SUCCESS"
                
                # Calculate earnings
                usd_earned = duration_hours * hourly_rate
                
                print(f"Job #{i}: {job_id[:12]}...")
                print(f"  Started: {started_text}")
                print(f"  Duration: {duration_text} ({duration_seconds}s = {duration_hours:.3f}h)")
                print(f"  Rate: {price_text} ({hourly_rate}/h)")
                print(f"  GPU: {gpu_text}")
                print(f"  Status: {status}")
                print(f"  💰 Earnings: ${usd_earned:.4f}")
                print()
                
                jobs.append({
                    "job_id": job_id,
                    "started": started_text,
                    "duration_text": duration_text,
                    "duration_seconds": duration_seconds,
                    "hourly_rate_usd": hourly_rate,
                    "usd_earned": usd_earned,
                    "gpu_type": gpu_text,
                    "status": status
                })
                
            except Exception as e:
                print(f"❌ Error parsing job row {i}: {str(e)}")
                continue
        
        print(f"\n✅ Successfully scraped {len(jobs)} jobs")
        
        # Calculate totals
        total_usd = sum(j['usd_earned'] for j in jobs if j['status'] == 'SUCCESS')
        completed = len([j for j in jobs if j['status'] == 'SUCCESS'])
        running = len([j for j in jobs if j['status'] == 'RUNNING'])
        
        print(f"\n📊 Summary:")
        print(f"  Total Jobs: {len(jobs)}")
        print(f"  Completed: {completed}")
        print(f"  Running: {running}")
        print(f"  💰 Total Earnings (completed): ${total_usd:.2f}")
        
        return jobs
        
    except Exception as e:
        print(f"❌ Error scraping Nosana dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Test with the node address provided
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    jobs = scrape_nosana_job_history(node_address)
