# Testing Enhanced Job Notifications in Telegram

## Step-by-Step Instructions

### 1. Find Your Telegram Bot
Your Telegram bot token is configured in the backend. To test notifications, you need to:

1. **Open Telegram** on your phone or desktop
2. **Search for your bot** - The bot username should be visible in your Telegram bot settings (BotFather)
3. **Send `/start`** to your bot

### 2. Get Your Chat ID
Once you've sent `/start` to the bot, run this command on the server:

```bash
cd /app/backend && python3 test_job_notifications_simple.py
```

The script will automatically detect your chat ID from recent messages and ask if you want to send test notifications.

### 3. Alternative: Manual Chat ID
If you know your chat ID, you can run:

```bash
cd /app/backend && python3 test_job_notifications_simple.py YOUR_CHAT_ID
```

Replace `YOUR_CHAT_ID` with your actual chat ID (a number like 123456789).

### 4. What You'll See

The script will send **5 sample job completion notifications** with different durations:

1. **90 seconds job** (1m 30s) - Quick job
2. **360 seconds job** (6m 0s) - Short job  
3. **1500 seconds job** (25m 0s) - Medium job
4. **3600 seconds job** (1h 0m) - Hourly job
5. **7200 seconds job** (2h 0m) - Long job

Each notification will show:
- 🎉 Job Completed - [Node Name]
- ⏱️ Duration: [formatted time]
- 💰 Payment: [X.XX NOS (~$X.XX USD)]
- [View Dashboard] link

### 5. Example Notification

```
🎉 Job Completed - Node Alpha

⏱️ Duration: 25m 0s
💰 Payment: 0.42 NOS (~$0.19 USD)

[View Dashboard]
```

### 6. How to Find Your Bot Token/Username

If you don't know your bot's username:

1. Check `/app/backend/.env` file for `TELEGRAM_BOT_TOKEN`
2. Go to Telegram and message **@BotFather**
3. Send `/mybots` command
4. Select your bot to see its username

### 7. Testing with Real App

To test with actual job completions:

1. **Create an account** on the app (https://node-pulse.preview.emergentagent.com)
2. **Add your nodes** to monitor
3. **Link Telegram account**:
   - Click Settings (Bell icon) in the app
   - Find "Telegram Notifications" section
   - Click "Link Telegram Account"
   - Copy the linking code
   - Send it to your bot in Telegram
4. **Wait for jobs to complete** - You'll automatically receive enhanced notifications

### 8. Notification Features

The enhanced notifications include:

✅ **Job Duration** - Automatically tracked from start to completion
✅ **Payment Estimate** - Based on GPU hourly rates and current NOS price
✅ **Live NOS Price** - Fetched from CoinGecko API
✅ **Dashboard Link** - Direct link to view node details on Nosana dashboard

### 9. Troubleshooting

**Bot not responding?**
```bash
# Check if Telegram bot service is running
sudo supervisorctl status telegram-bot

# Restart if needed
sudo supervisorctl restart telegram-bot

# Check logs
tail -f /var/log/supervisor/telegram-bot.*.log
```

**No notifications received?**
- Make sure you've sent `/start` to the bot first
- Verify your Telegram account is linked in the app
- Check backend logs for errors: `tail -f /var/log/supervisor/backend.err.log`

### 10. Ready to Test?

Once you've sent `/start` to your bot, simply run:

```bash
cd /app/backend && python3 test_job_notifications_simple.py
```

And follow the prompts! 🎉
