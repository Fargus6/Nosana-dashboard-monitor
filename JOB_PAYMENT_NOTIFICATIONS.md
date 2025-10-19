# Job Payment & Duration Tracking

## Overview
Enhanced Telegram notifications now include **job duration** and **estimated payment** information when a job completes on your Nosana nodes.

## Features

### 1. Job Duration Tracking
- **Start Time**: Automatically recorded when job status changes to `running`
- **Duration Calculation**: Calculated when job completes (status changes from `running` to `idle` or `queue`)
- **Human-Readable Format**: Displays as "5m 30s", "1h 45m", etc.

### 2. Payment Estimation
- **Live NOS Price**: Fetches current NOS token price from CoinGecko API
- **GPU-Based Calculation**: Uses Nosana market hourly rates
  - A100 80GB: $0.90/hr
  - RTX Pro 6000: $1.00/hr
  - H100: $1.50/hr
- **Dynamic Conversion**: Converts USD earnings to NOS based on current token price
- **Dual Display**: Shows both NOS amount and USD equivalent

### 3. Enhanced Telegram Notifications
When a job completes, you'll receive:
```
🎉 Job Completed - Node Name

⏱️ Duration: 5m 30s
💰 Payment: 0.25 NOS (~$0.12 USD)

[View Dashboard]
```

### 4. Firebase Push Notifications
- Remain simple: "✅ Job Completed - Node name completed a job"
- No duration/payment info (to keep notifications concise)

## How It Works

### Backend Logic Flow
1. **Job Starts** (status: idle/queue → running)
   - Store `job_start_time` in database
   - Send basic "Job Started" notification

2. **Job Completes** (status: running → idle/queue)
   - Calculate duration from stored start time
   - Fetch current NOS token price from CoinGecko
   - Calculate payment: `(hourly_rate × duration_hours) / nos_price`
   - Send Firebase push notification (basic)
   - Send enhanced Telegram notification (with duration & payment)
   - Clear start time and increment completed jobs counter

### Payment Calculation Example
```python
# Example: 10-minute job on A100
duration = 600 seconds (10 minutes)
hourly_rate = $0.90 (A100)
nos_price = $0.46 (from CoinGecko)

# Calculate
duration_hours = 600 / 3600 = 0.167 hours
usd_earned = $0.90 × 0.167 = $0.15
nos_payment = $0.15 / $0.46 = 0.33 NOS

# Result: "0.33 NOS (~$0.15 USD)"
```

## API Integration

### CoinGecko API
- **Endpoint**: `https://api.coingecko.com/api/v3/simple/price?ids=nosana&vs_currencies=usd`
- **Rate Limit**: Free tier, no API key required
- **Fallback**: If API fails, payment info is omitted from notification

### Nosana Dashboard
- **Link**: Each notification includes direct link to node dashboard
- **Format**: `https://dashboard.nosana.com/host/[node_address]`

## Database Schema Updates

### Node Document
```javascript
{
  // ... existing fields
  job_start_time: "2025-10-19T12:00:00Z",  // ISO timestamp
  job_count_completed: 15,                  // Total completed jobs
}
```

## Configuration

### GPU Type (Future Enhancement)
Current implementation uses A100 default rate ($0.90/hr). To customize:
1. Modify `calculate_job_payment()` in `server.py`
2. Add GPU type field to Node model
3. Update calculation logic to use node-specific GPU type

### Notification Preferences
- Controlled by existing `notify_job_completed` preference
- Applied to both Firebase push and Telegram notifications

## Testing

### Manual Testing
1. Start a job on your node (status → running)
2. Wait for job to complete (status → idle/queue)
3. Check Telegram for enhanced notification
4. Verify:
   - Duration is reasonable
   - Payment calculation matches expected earnings
   - Dashboard link works

### Backend Testing
```bash
# Test NOS price fetch
curl http://localhost:8001/api/test-nos-price

# Test job status transition
# (Requires actual node with running jobs)
```

## Troubleshooting

### No Duration Shown
**Issue**: Notification shows "Duration: Unknown"
**Cause**: Job start time wasn't recorded
**Solution**: Ensure `refresh_all_node_status` runs regularly to catch job starts

### No Payment Info
**Issue**: Payment info missing from notification
**Cause**: CoinGecko API failed or rate limited
**Solution**: Check backend logs for API errors; wait and retry

### Incorrect Payment Amount
**Issue**: Payment doesn't match expected earnings
**Cause**: Using default A100 rate, or NOS price fluctuation
**Solution**: 
1. Verify actual GPU type matches A100 rate
2. Check CoinGecko for current NOS price
3. Remember: Estimates don't account for Nosana platform fees

## Limitations

1. **Estimate Only**: Payment is estimated based on market rates, not actual blockchain transactions
2. **No Platform Fees**: Calculation doesn't deduct Nosana platform fees (if any)
3. **Price Volatility**: NOS price can fluctuate between job start and completion
4. **Default GPU Rate**: Currently assumes A100 GPU rate for all nodes
5. **Missed Job Starts**: If app isn't running when job starts, duration won't be tracked

## Future Enhancements

### Planned Features
- [ ] Per-node GPU type configuration
- [ ] Blockchain transaction parsing for actual payments
- [ ] Historical job statistics and earnings reports
- [ ] Weekly/monthly earnings summaries
- [ ] Custom notification templates
- [ ] Multi-currency display (EUR, etc.)

### Advanced Options
- Parse actual payment from Solana blockchain transactions
- Add total daily/weekly earnings summaries
- Create earnings dashboard in frontend
- Support custom GPU hourly rates per node

## Related Documentation
- [TELEGRAM_BOT_INTEGRATION.md](./TELEGRAM_BOT_INTEGRATION.md) - Telegram setup
- [README.md](./README.md) - General app documentation
- [NOS_BALANCE_FIX.md](./NOS_BALANCE_FIX.md) - Balance display fixes

## Support
For issues or questions:
1. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
2. Verify Telegram bot is running: `sudo supervisorctl status telegram-bot`
3. Test CoinGecko API: `curl https://api.coingecko.com/api/v3/simple/price?ids=nosana&vs_currencies=usd`
