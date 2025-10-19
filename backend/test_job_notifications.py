#!/usr/bin/env python3
"""
Test script to send sample job completion notifications to Telegram
Simulates various job scenarios to show how notifications look
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Bot
from telegram.constants import ParseMode
import requests

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client.nosana_monitor

# Telegram bot
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)


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
                print(f"💰 NOS Token Price: ${price:.4f} USD")
                return float(price)
    except Exception as e:
        print(f"Error fetching NOS price: {str(e)}")
    return 0.46  # Fallback price


def calculate_job_payment(duration_seconds, nos_price_usd, gpu_type="A100"):
    """Calculate estimated NOS payment for a job"""
    try:
        gpu_rates = {
            "A100": 0.90,
            "Pro6000": 1.00,
            "H100": 1.50,
            "default": 0.90
        }
        
        hourly_rate_usd = gpu_rates.get(gpu_type, gpu_rates["default"])
        duration_hours = duration_seconds / 3600.0
        usd_earned = hourly_rate_usd * duration_hours
        
        if nos_price_usd and nos_price_usd > 0:
            nos_payment = usd_earned / nos_price_usd
            return nos_payment
        
        return None
    except Exception as e:
        print(f"Error calculating payment: {str(e)}")
        return None


def format_duration(seconds):
    """Format duration in seconds to human-readable format"""
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


async def send_test_notification(user_id, node_name, node_address, duration_seconds, gpu_type="A100"):
    """Send a test job completion notification"""
    try:
        # Get user's Telegram chat ID
        telegram_account = await db.telegram_accounts.find_one({"user_id": user_id})
        
        if not telegram_account:
            print(f"❌ No Telegram account linked for user {user_id}")
            return False
        
        chat_id = telegram_account.get('chat_id')
        if not chat_id:
            print(f"❌ No chat_id found for user {user_id}")
            return False
        
        # Get NOS price
        nos_price = await get_nos_token_price()
        
        # Calculate payment
        nos_payment = calculate_job_payment(duration_seconds, nos_price, gpu_type)
        
        # Format duration
        duration_str = format_duration(duration_seconds)
        
        # Build notification message
        telegram_message = f"🎉 **Job Completed - {node_name}**\n\n"
        telegram_message += f"⏱️ Duration: {duration_str}"
        
        if nos_payment:
            usd_value = nos_payment * nos_price
            telegram_message += f"\n💰 Payment: {nos_payment:.2f} NOS (~${usd_value:.2f} USD)"
        
        telegram_message += f"\n\n[View Dashboard](https://dashboard.nosana.com/host/{node_address})"
        
        # Send to Telegram
        await telegram_bot.send_message(
            chat_id=chat_id,
            text=telegram_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        print(f"✅ Sent notification for {node_name} ({duration_str})")
        return True
        
    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")
        return False


async def main():
    """Main test function"""
    print("=" * 70)
    print("🧪 Testing Enhanced Job Completion Notifications")
    print("=" * 70)
    print()
    
    # Find user with email test@prod.com
    user = await db.users.find_one({"email": "test@prod.com"})
    
    if not user:
        print("❌ User not found: test@prod.com")
        return
    
    user_id = user['id']
    print(f"👤 Found user: {user['email']} (ID: {user_id})")
    print()
    
    # Check if user has Telegram linked
    telegram_account = await db.telegram_accounts.find_one({"user_id": user_id})
    
    if not telegram_account:
        print("❌ No Telegram account linked. Please link your Telegram account first.")
        print("   Use /start and /link commands in the Telegram bot.")
        return
    
    print(f"✅ Telegram account linked: Chat ID {telegram_account.get('chat_id')}")
    print()
    
    # Get user's nodes
    nodes = await db.nodes.find({"user_id": user_id}).to_list(100)
    
    if not nodes:
        print("❌ No nodes found for user")
        return
    
    print(f"📡 Found {len(nodes)} node(s)")
    print()
    
    # Test scenarios with different durations
    test_scenarios = [
        {"name": "Quick Job", "duration": 120, "gpu": "A100"},  # 2 minutes
        {"name": "Short Job", "duration": 450, "gpu": "A100"},  # 7.5 minutes
        {"name": "Medium Job", "duration": 1800, "gpu": "A100"},  # 30 minutes
        {"name": "Long Job", "duration": 5400, "gpu": "A100"},  # 1.5 hours
        {"name": "Extended Job", "duration": 10800, "gpu": "A100"},  # 3 hours
    ]
    
    print("📤 Sending test notifications...")
    print()
    
    # Send test notifications using actual node data
    for i, scenario in enumerate(test_scenarios):
        # Use actual node or create test node name
        if i < len(nodes):
            node = nodes[i]
            node_name = node.get('name') or f"{node['address'][:8]}..."
            node_address = node['address']
        else:
            node_name = f"Test Node {i+1}"
            node_address = "9DcLW6JkuanvWP2CbKsohChFWGCEiTnAGxA4xdAYHVNq"
        
        print(f"📨 Sending: {scenario['name']} ({format_duration(scenario['duration'])})")
        
        await send_test_notification(
            user_id=user_id,
            node_name=node_name,
            node_address=node_address,
            duration_seconds=scenario['duration'],
            gpu_type=scenario['gpu']
        )
        
        # Wait a bit between messages to avoid rate limiting
        await asyncio.sleep(2)
    
    print()
    print("=" * 70)
    print("✅ Test notifications sent!")
    print("Check your Telegram app to see how they look.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
