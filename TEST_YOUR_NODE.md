# 🚀 Test Job Notifications for Your Node

## Your Node Information
- **Address**: `7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH`
- **Bot Username**: `@NosNode_bot`
- **Bot Token Suffix**: `51CE4E95` ✅

## Step-by-Step Testing Guide

### Step 1: Message the Bot
1. Open Telegram
2. Search for: **@NosNode_bot**
3. Send: **/start**
4. The bot will respond with a linking code

### Step 2: Get Your Chat ID

**Option A - From Bot Response:**
When you send /start, the bot message will include information. Your chat ID is a number like `123456789`.

**Option B - Use Web API:**
Visit this URL in your browser (replace with your actual bot token):
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

Look for: `"chat":{"id":YOUR_CHAT_ID}`

**Option C - Use Script:**
After sending /start, run:
```bash
cd /app/backend && sudo supervisorctl stop telegram-bot && python3 << 'EOF'
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv('.env')
bot = Bot(token=os.environ.get('TELEGRAM_BOT_TOKEN'))

async def show_chats():
    updates = await bot.get_updates()
    for u in updates[-3:]:
        if u.message:
            print(f"Chat ID: {u.message.chat.id}")

asyncio.run(show_chats())
EOF
sudo supervisorctl start telegram-bot
```

### Step 3: Run Test Script

Once you have your chat ID, run:

```bash
cd /app/backend && python3 test_my_node.py YOUR_CHAT_ID
```

Replace `YOUR_CHAT_ID` with your actual chat ID (e.g., `123456789`)

### Step 4: View Notifications

You will receive **5 test notifications** with different job durations:

1. **2 minutes** - Quick job
2. **10 minutes** - Short job
3. **30 minutes** - Medium job
4. **1 hour** - Standard job
5. **2.5 hours** - Long job

Each notification shows:
```
🎉 Job Completed - Main Production Node

⏱️ Duration: 30m 0s
💰 Payment: 0.42 NOS (~$0.19 USD)

[View Dashboard]
```

## Example Commands

### If your chat ID is 987654321:
```bash
cd /app/backend && python3 test_my_node.py 987654321
```

### Check bot status:
```bash
sudo supervisorctl status telegram-bot
```

### View bot logs:
```bash
tail -f /var/log/supervisor/telegram-bot.err.log
```

## What Happens in Production

Once you link your Telegram account in the app:

1. **Job Starts** → Bot tracks start time
2. **Job Completes** → Bot calculates:
   - Duration (from start to completion)
   - Payment (based on A100 rate: $0.90/hr)
   - Current NOS price (from CoinGecko)
3. **Notification Sent** → You get enhanced message with all details

## Troubleshooting

**Bot doesn't respond?**
```bash
sudo supervisorctl restart telegram-bot
tail -f /var/log/supervisor/telegram-bot.err.log
```

**Wrong bot?**
Your bot is: **@NosNode_bot** (ID: 7450691415)

**Script fails?**
Make sure telegram-bot service is running:
```bash
sudo supervisorctl status telegram-bot
```

## Ready?

1. ✅ Open Telegram
2. ✅ Message @NosNode_bot
3. ✅ Send /start
4. ✅ Get your Chat ID
5. ✅ Run: `python3 test_my_node.py YOUR_CHAT_ID`
6. ✅ Check your Telegram for 5 sample notifications!

---

**Note**: The test uses your actual node address `7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH` and creates realistic job completion notifications with live NOS pricing.
