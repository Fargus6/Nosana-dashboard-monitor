import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timezone
import pytz

async def scrape_and_show_earnings(node_address):
    """Scrape Nosana dashboard and show actual payment calculations"""
    
    print(f"\n{'='*80}")
    print(f"EARNINGS ANALYSIS FOR NODE: {node_address}")
    print(f"{'='*80}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to node's job history
        url = f"https://explorer.nosana.io/nodes/{node_address}/jobs"
        print(f"Fetching data from: {url}\n")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Find all job rows
            job_rows = await page.query_selector_all("div.grid.grid-cols-4.gap-4.border-t")
            
            if not job_rows:
                print("❌ No job history found on dashboard")
                await browser.close()
                return
            
            print(f"Found {len(job_rows)} jobs on dashboard\n")
            
            jobs_data = []
            
            for idx, row in enumerate(job_rows[:20], 1):  # Check first 20 jobs
                try:
                    # Get all columns
                    columns = await row.query_selector_all("div")
                    
                    if len(columns) >= 4:
                        # Column 0: Time (relative)
                        time_elem = await columns[0].query_selector("span")
                        relative_time = await time_elem.inner_text() if time_elem else "Unknown"
                        
                        # Column 1: Duration
                        duration_elem = await columns[1].query_selector("span")
                        duration = await duration_elem.inner_text() if duration_elem else "Unknown"
                        
                        # Column 2: Rate ($/hour)
                        rate_elem = await columns[2].query_selector("span")
                        rate = await rate_elem.inner_text() if rate_elem else "Unknown"
                        
                        # Column 3: Payment (THIS IS THE ACTUAL PAYMENT AMOUNT)
                        payment_elem = await columns[3].query_selector("span")
                        payment_text = await payment_elem.inner_text() if payment_elem else "Unknown"
                        
                        # Extract numeric value from payment (e.g., "$0.176" -> 0.176)
                        payment_value = 0.0
                        if payment_text and payment_text != "Unknown":
                            payment_value = float(payment_text.replace("$", "").replace(",", "").strip())
                        
                        job_info = {
                            "relative_time": relative_time,
                            "duration": duration,
                            "rate": rate,
                            "payment": payment_value,
                            "payment_display": payment_text
                        }
                        
                        jobs_data.append(job_info)
                        
                        print(f"Job #{idx}:")
                        print(f"  Time: {relative_time}")
                        print(f"  Duration: {duration}")
                        print(f"  Rate: {rate}")
                        print(f"  💰 Payment: ${payment_value:.3f}")
                        print()
                        
                except Exception as e:
                    print(f"⚠️  Error parsing job #{idx}: {e}")
                    continue
            
            await browser.close()
            
            # Now calculate statistics
            print("\n" + "="*80)
            print("EARNINGS CALCULATIONS (Based on Dashboard Payment Amounts)")
            print("="*80 + "\n")
            
            # Get current time in UTC
            now_utc = datetime.now(timezone.utc)
            
            # Calculate totals
            today_total = 0.0
            yesterday_total = 0.0
            this_month_total = 0.0
            overall_total = 0.0
            
            # For demonstration, let's assume:
            # - Jobs with "hours ago" or "minutes ago" are today
            # - Jobs with "1 day ago" are yesterday
            # - All jobs shown contribute to this month and overall
            
            today_jobs = []
            yesterday_jobs = []
            
            for job in jobs_data:
                payment = job["payment"]
                overall_total += payment
                this_month_total += payment  # Assuming all visible jobs are from this month
                
                time_text = job["relative_time"].lower()
                
                if "hour" in time_text or "minute" in time_text:
                    today_total += payment
                    today_jobs.append(job)
                elif "1 day" in time_text or "day ago" in time_text:
                    # Check if exactly 1 day
                    if time_text.startswith("1 "):
                        yesterday_total += payment
                        yesterday_jobs.append(job)
            
            # Display results
            print("📊 TODAY'S EARNINGS:")
            print(f"   Jobs: {len(today_jobs)}")
            for job in today_jobs:
                print(f"   • {job['relative_time']}: ${job['payment']:.3f} ({job['duration']} @ {job['rate']})")
            print(f"   ➡️  TOTAL TODAY: ${today_total:.3f}\n")
            
            print("📊 YESTERDAY'S EARNINGS:")
            print(f"   Jobs: {len(yesterday_jobs)}")
            for job in yesterday_jobs:
                print(f"   • {job['relative_time']}: ${job['payment']:.3f} ({job['duration']} @ {job['rate']})")
            print(f"   ➡️  TOTAL YESTERDAY: ${yesterday_total:.3f}\n")
            
            print("📊 THIS MONTH'S EARNINGS:")
            print(f"   Jobs shown: {len(jobs_data)}")
            print(f"   ➡️  TOTAL THIS MONTH: ${this_month_total:.3f}\n")
            
            print("📊 OVERALL EARNINGS (from visible jobs):")
            print(f"   Jobs shown: {len(jobs_data)}")
            print(f"   ➡️  TOTAL OVERALL: ${overall_total:.3f}\n")
            
            print("="*80)
            print("✅ These are ACTUAL payment amounts from the dashboard")
            print("✅ No formulas used - just direct scraping and simple addition")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            await browser.close()

if __name__ == "__main__":
    node_address = "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"
    asyncio.run(scrape_and_show_earnings(node_address))
