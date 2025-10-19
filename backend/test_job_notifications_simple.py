#!/usr/bin/env python3
"""
Simplified test script to send sample job completion notifications
Requires only TELEGRAM_BOT_TOKEN and your chat ID
"""

import asyncio
import os
from pathlib import Path
from telegram import Bot
from telegram.constants import ParseMode
import requests

# Load environment
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')


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
                return float(price)
    except Exception:
        pass
    return 0.46  # Fallback


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


async def send_sample_notifications(chat_id):
    """Send sample notifications to Telegram"""
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    print("=" * 70)
    print("🧪 Sending Sample Job Completion Notifications")
    print("=" * 70)
    print(f"📱 Sending to Chat ID: {chat_id}")
    print()
    
    # Get NOS price
    nos_price = await get_nos_token_price()
    print(f"💰 Current NOS Price: ${nos_price:.4f} USD")
    print()
    
    # Test scenarios
    test_jobs = [
        {"name": "Node Alpha", "duration": 90, "address": "9DcLW6JkuanvWP2CbKsohChFWGCEiTnAGxA4xdAYHVNq"},
        {"name": "Node Beta", "duration": 360, "address": "9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV"},
        {"name": "Node Gamma", "duration": 1500, "address": "11111111111111111111111111111112"},
        {"name": "GPU-A100-01", "duration": 3600, "address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
        {"name": "Production Node", "duration": 7200, "address": "9DcLW6JkuanvWP2CbKsohChFWGCEiTnAGxA4xdAYHVNq"},
    ]
    
    for i, job in enumerate(test_jobs, 1):
        print(f"📨 [{i}/{len(test_jobs)}] Sending: {job['name']} ({format_duration(job['duration'])})")
        
        # Calculate payment
        nos_payment = calculate_job_payment(job['duration'], nos_price)
        
        # Build message
        telegram_message = f"🎉 **Job Completed - {job['name']}**\n\n"
        telegram_message += f"⏱️ Duration: {format_duration(job['duration'])}"
        
        if nos_payment:
            usd_value = nos_payment * nos_price
            telegram_message += f"\n💰 Payment: {nos_payment:.2f} NOS (~${usd_value:.2f} USD)"
        
        telegram_message += f"\n\n[View Dashboard](https://dashboard.nosana.com/host/{job['address']})"
        
        try:
            # Send message
            await telegram_bot.send_message(
                chat_id=chat_id,
                text=telegram_message,
                parse_mode=ParseMode.MARKDOWN
            )
            print(f"   ✅ Sent successfully")
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
        
        # Wait between messages
        await asyncio.sleep(2)
    
    print()
    print("=" * 70)
    print("✅ All sample notifications sent!")
    print("Check your Telegram app to see how they look.")
    print("=" * 70)


async def main():
    """Main function"""
    print()
    print("To use this script, you need to:")
    print("1. Get your Telegram Chat ID by messaging /start to your bot")
    print("2. Then run: python3 test_job_notifications_simple.py YOUR_CHAT_ID")
    print()
    print("Example: python3 test_job_notifications_simple.py 123456789")
    print()
    
    # Check if chat ID provided as argument
    import sys
    if len(sys.argv) < 2:
        print("❌ Please provide your Telegram Chat ID as an argument")
        print()
        
        # Try to get it from the bot
        print("📱 Attempting to get your chat ID from bot updates...")
        
        if TELEGRAM_BOT_TOKEN:
            try:
                telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
                updates = await telegram_bot.get_updates()
                
                if updates:
                    print(f"\n✅ Found {len(updates)} recent message(s):")
                    for update in updates[-5:]:  # Show last 5
                        if update.message:
                            chat_id = update.message.chat.id
                            username = update.message.chat.username or "N/A"
                            text = update.message.text or ""
                            print(f"   Chat ID: {chat_id}, Username: @{username}, Message: {text[:30]}")
                    
                    # Use the most recent chat ID
                    latest_chat_id = updates[-1].message.chat.id
                    print(f"\n💡 Using most recent chat ID: {latest_chat_id}")
                    print()
                    
                    response = input("Send test notifications to this chat? (yes/no): ")
                    if response.lower() in ['yes', 'y']:
                        await send_sample_notifications(latest_chat_id)
                        return
                else:
                    print("   ℹ️ No messages found. Send /start to the bot first.")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        return
    
    # Use provided chat ID
    chat_id = sys.argv[1]
    
    try:
        chat_id = int(chat_id)
    except ValueError:
        print(f"❌ Invalid chat ID: {chat_id}")
        return
    
    await send_sample_notifications(chat_id)


if __name__ == "__main__":
    asyncio.run(main())
