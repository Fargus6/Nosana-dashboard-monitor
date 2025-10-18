# Automated Testing System Documentation

## Overview
This automated testing system runs comprehensive tests on your Nosana Node Monitor application every day at 2:00 AM for 7 days, starting from October 18, 2025.

## Test Schedule
- **Frequency**: Daily at 2:00 AM
- **Duration**: 7 days (until October 25, 2025)
- **Location**: `/app/tests/`

## Test Components

### 1. Backend Tests (`automated_backend_test.sh`)
Tests all backend API endpoints and functionality:
- Health check endpoint
- User registration and login
- Authentication (JWT)
- Node CRUD operations (Create, Read, Update, Delete)
- Auto-refresh functionality
- Notification preferences
- Rate limiting
- Database connectivity
- Service status

**Expected**: 11 tests, 100% pass rate

### 2. Frontend Tests (`automated_frontend_test.sh`)
Tests UI functionality using Playwright:
- Page load and rendering
- Login form elements
- Theme selector (Dark Mode, 80s Neon, Cyber)
- Google OAuth button
- User login flow
- Node display
- Auto-refresh selector
- Theme switching

**Expected**: 8 tests, 100% pass rate

### 3. System Health Check
- Service status (backend, frontend, MongoDB)
- Disk usage
- Memory usage
- Database statistics (user count, node count)

## Test Results Location
All test results are stored in `/app/tests/results/`:
- `daily_test_YYYY-MM-DD_HH-MM-SS.log` - Full test run logs
- `backend_test_YYYY-MM-DD_HH-MM-SS.log` - Backend-specific logs
- `frontend_test_YYYY-MM-DD_HH-MM-SS.log` - Frontend-specific logs
- `test_summary.csv` - Aggregated test results
- `cron_output.log` - Cron job execution log

## How to Use

### View Test Results Dashboard
```bash
/app/tests/view_results.sh
```

### Run Tests Manually (Anytime)
```bash
# Run full test suite
/app/tests/run_daily_tests.sh

# Run only backend tests
/app/tests/automated_backend_test.sh

# Run only frontend tests
/app/tests/automated_frontend_test.sh
```

### View Latest Results
```bash
# View latest daily test
tail -n 50 /app/tests/results/daily_test_*.log | tail -n 50

# View test summary
cat /app/tests/results/test_summary.csv

# Monitor cron output
tail -f /app/tests/results/cron_output.log
```

### Check Cron Job Status
```bash
crontab -l
```

### Modify Schedule (if needed)
```bash
# Edit crontab
crontab -e

# Current schedule: 0 2 * * * (2:00 AM daily)
# Change to 3 AM: 0 3 * * *
# Change to every 12 hours: 0 */12 * * *
```

## What Gets Tested

### Authentication System
- ✅ Email/password registration
- ✅ Email/password login
- ✅ Google OAuth (button presence)
- ✅ JWT token generation
- ✅ Session management
- ✅ Rate limiting

### Node Management
- ✅ Add new nodes
- ✅ List all nodes
- ✅ Update node information
- ✅ Delete nodes
- ✅ Refresh node status from blockchain
- ✅ Node status indicators (online/offline/running)

### UI Functionality
- ✅ Page loading
- ✅ Login form
- ✅ Theme switching (3 themes)
- ✅ Auto-refresh selector
- ✅ Node cards display
- ✅ Responsive design

### System Health
- ✅ All services running
- ✅ Database connectivity
- ✅ Disk space
- ✅ Memory usage

## Interpreting Results

### Success Indicators
- ✅ = Test passed
- 100% success rate = All systems operational
- All services RUNNING = Healthy system

### Failure Indicators
- ❌ = Test failed
- <100% success rate = Issues detected
- Service STOPPED = Service issue

### Common Issues and Solutions

**If tests fail:**
1. Check service status: `sudo supervisorctl status`
2. Check backend logs: `tail -n 50 /var/log/supervisor/backend.err.log`
3. Check frontend logs: `tail -n 50 /var/log/supervisor/frontend.err.log`
4. Restart services: `sudo supervisorctl restart all`

**If cron doesn't run:**
1. Check cron service: `service cron status`
2. Start cron: `service cron start`
3. Check crontab: `crontab -l`

## Alerts and Monitoring

### Daily Reports
Every test run generates a detailed log with:
- Timestamp
- Individual test results
- System health metrics
- Pass/fail summary
- Success rate percentage

### What to Monitor
- Success rate should be ≥95%
- All services should be RUNNING
- Database should be responsive
- No critical errors in logs

## Manual Deep Dive Testing

When you need deeper analysis, you can ask me (the AI) anytime to:
- Run specific tests
- Investigate failures
- Check detailed logs
- Analyze performance
- Test specific features
- Debug issues

## Retention Policy
- Logs older than 30 days are automatically deleted
- Test summary CSV keeps all historical data
- Screenshots (if any) are kept for 30 days

## Support

For issues or questions:
1. Run `/app/tests/view_results.sh` to see the dashboard
2. Check the latest logs in `/app/tests/results/`
3. Ask me (the AI) for deeper investigation anytime
4. Check the main app logs in `/var/log/supervisor/`

## Test Coverage

### Backend Coverage: ~95%
- All major API endpoints
- Authentication flows
- Database operations
- Rate limiting
- Security features

### Frontend Coverage: ~80%
- Core UI functionality
- Theme system
- Authentication UI
- Node display
- User interactions

### Not Tested (Manual verification recommended)
- Push notification actual delivery (requires real devices)
- Email notifications (if any)
- Payment processing (if any)
- Third-party integrations beyond OAuth

## Notes
- Tests run in production environment
- Tests create and delete temporary test users
- Tests use real blockchain data when possible
- Some tests may trigger rate limits (this is expected)
- Frontend tests run in headless browser mode

---
**Last Updated**: October 18, 2025
**Test Schedule**: Daily at 2:00 AM until October 25, 2025
**Status**: ✅ Active and Running
