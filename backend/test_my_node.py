#!/usr/bin/env python3
"""
Custom test for specific node: 7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH
Sends sample job completion notifications to Telegram
"""

import asyncio
import os
import sys
from pathlib import Path
from telegram import Bot
from telegram.constants import ParseMode
import requests

# Load environment
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# User's node
NODE_ADDRESS = "7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH"
NODE_NAME = "Main Production Node"


async def get_nos_token_price():
    """Fetch current NOS token price from CoinGecko"""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=nosana&vs_currencies=usd",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            price = data.get('nosana', {}).get('usd')
            if price:
                print(f"💰 Current NOS Price: ${price:.4f} USD")
                return float(price)
    except Exception as e:
        print(f"⚠️ Error fetching NOS price: {str(e)}")
    
    # Fallback price
    fallback = 0.46
    print(f"💰 Using fallback NOS Price: ${fallback:.4f} USD")
    return fallback


def calculate_job_payment(duration_seconds, nos_price_usd):
    """Calculate estimated NOS payment (A100 rate: $0.90/hr)"""
    hourly_rate_usd = 0.90  # A100 rate
    duration_hours = duration_seconds / 3600.0
    usd_earned = hourly_rate_usd * duration_hours
    
    if nos_price_usd and nos_price_usd > 0:
        nos_payment = usd_earned / nos_price_usd
        return nos_payment
    return None


def format_duration(seconds):
    """Format duration to human-readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"


async def send_test_notification(chat_id, node_name, node_address, duration_seconds):
    """Send a test job completion notification"""
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return False
    
    try:
        telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get NOS price
        nos_price = await get_nos_token_price()
        
        # Calculate payment
        nos_payment = calculate_job_payment(duration_seconds, nos_price)
        
        # Format duration
        duration_str = format_duration(duration_seconds)
        
        # Build notification message (same format as production)
        telegram_message = f"🎉 **Job Completed - {node_name}**\n\n"
        telegram_message += f"⏱️ Duration: {duration_str}"
        
        if nos_payment:
            usd_value = nos_payment * nos_price
            telegram_message += f"\n💰 Payment: {nos_payment:.2f} NOS (~${usd_value:.2f} USD)"
        
        telegram_message += f"\n\n[View Dashboard](https://dashboard.nosana.com/host/{node_address})"
        
        # Send to Telegram
        result = await telegram_bot.send_message(
            chat_id=chat_id,
            text=telegram_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        print(f"✅ Notification sent successfully!")
        print(f"   Message ID: {result.message_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")
        return False


async def main():
    """Main test function"""
    print()
    print("=" * 70)
    print("🧪 Custom Job Notification Test")
    print("=" * 70)
    print(f"📡 Node: {NODE_ADDRESS}")
    print(f"🏷️  Name: {NODE_NAME}")
    print()
    
    # Check if chat ID provided
    if len(sys.argv) < 2:
        print("❌ Please provide your Telegram Chat ID")
        print()
        print("How to get your Chat ID:")
        print("1. Open Telegram")
        print("2. Send /start to your bot")
        print("3. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        print("4. Look for 'chat':{'id': YOUR_CHAT_ID}")
        print()
        print("Then run:")
        print(f"   python3 {sys.argv[0]} YOUR_CHAT_ID")
        print()
        
        # Try to get recent updates
        if TELEGRAM_BOT_TOKEN:
            print("🔍 Checking for recent messages...")
            try:
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                updates = await bot.get_updates()
                
                if updates:
                    print(f"✅ Found {len(updates)} message(s):")
                    seen_chats = set()
                    for update in reversed(updates[-5:]):
                        if update.message and update.message.chat.id not in seen_chats:
                            chat_id = update.message.chat.id
                            first_name = update.message.chat.first_name or "Unknown"
                            username = update.message.chat.username or "N/A"
                            text = update.message.text or ""
                            print(f"   - Chat ID: {chat_id}")
                            print(f"     Name: {first_name} (@{username})")
                            print(f"     Last message: {text[:40]}")
                            seen_chats.add(chat_id)
                    
                    if seen_chats:
                        latest_chat_id = list(seen_chats)[0]
                        print()
                        response = input(f"Send test notifications to Chat ID {latest_chat_id}? (yes/no): ")
                        if response.lower() in ['yes', 'y']:
                            chat_id = latest_chat_id
                        else:
                            return
                    else:
                        print()
                        print("⚠️ Please send /start to your bot first, then run this script again")
                        return
                else:
                    print("⚠️ No messages found. Please send /start to your bot first.")
                    return
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return
        else:
            return
    else:
        # Use provided chat ID
        try:
            chat_id = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid chat ID: {sys.argv[1]}")
            return
    
    print()
    print("=" * 70)
    print("📤 Sending Test Notifications")
    print("=" * 70)
    print()
    
    # Test scenarios based on real job durations
    test_jobs = [
        {"desc": "Quick job (2 minutes)", "duration": 120},
        {"desc": "Short job (10 minutes)", "duration": 600},
        {"desc": "Medium job (30 minutes)", "duration": 1800},
        {"desc": "Standard job (1 hour)", "duration": 3600},
        {"desc": "Long job (2.5 hours)", "duration": 9000},
    ]
    
    for i, job in enumerate(test_jobs, 1):
        print(f"📨 [{i}/{len(test_jobs)}] {job['desc']}")
        print(f"   Duration: {format_duration(job['duration'])}")
        
        success = await send_test_notification(
            chat_id=chat_id,
            node_name=NODE_NAME,
            node_address=NODE_ADDRESS,
            duration_seconds=job['duration']
        )
        
        if not success:
            print(f"   ⚠️ Failed to send notification {i}")
        
        print()
        
        # Wait between messages
        if i < len(test_jobs):
            await asyncio.sleep(2)
    
    print("=" * 70)
    print("✅ Test Complete!")
    print("Check your Telegram app to see the notifications.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())
