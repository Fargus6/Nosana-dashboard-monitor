# Real-Time Job Notification Setup Guide

## ✅ Test Complete - Setting Up for Production

You've successfully tested the enhanced job notifications! Now let's set up your account for real-time monitoring.

## Setup Steps

### Step 1: Create Your Account
1. Go to: https://nosanamonitor.preview.emergentagent.com
2. Click **Register** (top right)
3. Enter your email and create a strong password
4. Click **Register**

### Step 2: Add Your Node
1. After logging in, click **"+ Add Node"**
2. Enter your node address: `7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH`
3. Give it a name (e.g., "Main Production Node")
4. Click **Add Node**

### Step 3: Link Your Telegram Account
1. Click the **Bell icon** (⚙️ Settings) in the top right
2. Scroll down to **"Telegram Notifications"** section
3. Enter your linking code: `C05A25EF`
4. Click **"Link Account"**
5. You should see: "✅ Telegram account linked successfully!"

### Step 4: Configure Notification Preferences
In the Settings modal, you can enable/disable:
- ✅ Job Started notifications
- ✅ Job Completed notifications (with duration & payment)
- ✅ Node Offline alerts
- ✅ Node Online alerts
- ✅ Low SOL balance warnings

**Recommended:** Keep all enabled

### Step 5: Set Auto-Refresh Interval
- Choose your preferred refresh interval (1, 2, 3, or 10 minutes)
- **Recommended:** 2-3 minutes for real-time updates without excessive API calls

## What Happens Next

Once set up, the system will automatically:

### When a Job Starts:
```
🚀 Job Started
Main Production Node started processing a job
```

### When a Job Completes:
```
🎉 Job Completed - Main Production Node

⏱️ Duration: 45m 30s
💰 Payment: 1.46 NOS (~$0.68 USD)

[View Dashboard]
```

### Other Automatic Notifications:
- ⚠️ Node goes offline
- ✅ Node comes back online  
- 🟡 SOL balance drops below 0.006

## How It Works

### Backend Monitoring:
1. **Every [X] minutes** (your refresh interval):
   - Checks all your nodes on Solana blockchain
   - Detects status changes (idle → running → idle)
   
2. **Job Start Detection:**
   - When status changes to `running`
   - Stores start timestamp
   - Sends "Job Started" notification
   
3. **Job Completion Detection:**
   - When status changes from `running` to `idle/queue`
   - Calculates duration from stored timestamp
   - Fetches live NOS price from CoinGecko
   - Calculates payment: `(hourly_rate × duration) / nos_price`
   - Sends enhanced Telegram notification

### Payment Calculation:
- **Default GPU Rate:** $0.90/hr (A100 80GB)
- **Live NOS Price:** Fetched from CoinGecko API
- **Formula:** `Payment in NOS = (Rate × Hours) / NOS_Price`

## Your Setup Summary

✅ **Bot:** @NosNode_bot  
✅ **Chat ID:** 477905388  
✅ **Username:** @Fargus6  
✅ **Linking Code:** C05A25EF  
✅ **Node:** 7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH  

## Testing Real-Time Notifications

Once everything is linked:

1. **Check Current Status:**
   - Your node will show current status in the app
   - Balances will be displayed (SOL & NOS)

2. **Wait for Job Completion:**
   - System auto-refreshes every X minutes
   - When your node completes a job, you'll get the notification
   - No action needed - fully automatic!

3. **Manual Refresh:**
   - Click "Refresh from Blockchain" anytime
   - Forces immediate status check

## Troubleshooting

### No Notifications?

**Check Linking:**
```bash
cd /app/backend && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('.env')
client = AsyncIOMotorClient(os.getenv('MONGO_URL'))
db = client.test_database

async def check():
    account = await db.telegram_accounts.find_one({"chat_id": 477905388})
    if account:
        print(f"✅ Linked to user: {account.get('user_id')}")
    else:
        print("❌ Not linked yet. Use code C05A25EF in app.")

asyncio.run(check())
EOF
```

**Check Bot Status:**
```bash
sudo supervisorctl status telegram-bot
```

**View Logs:**
```bash
tail -f /var/log/supervisor/backend.err.log | grep -i notification
```

### Notifications Not Working After Job Completion?

1. Check auto-refresh is enabled
2. Verify notification preferences are turned on
3. Check backend logs for errors
4. Ensure node status is being tracked correctly

## Advanced: Customize GPU Rate

If your node uses a different GPU type, update the calculation in `/app/backend/server.py`:

In the `calculate_job_payment()` function, you can change:
```python
gpu_rates = {
    "A100": 0.90,      # Your current default
    "Pro6000": 1.00,
    "H100": 1.50,
}
```

Or add a GPU type field to your node in the database.

## Next Steps

1. ✅ Register account on the web app
2. ✅ Add your node
3. ✅ Link Telegram with code `C05A25EF`
4. ✅ Enable notifications in Settings
5. ✅ Wait for jobs to complete naturally
6. ✅ Check Telegram for real-time notifications!

## Support

If you encounter any issues:
- Check this guide first
- Review backend logs
- Verify bot is running
- Test with manual refresh

The system is now production-ready and will automatically track all your job completions! 🚀
