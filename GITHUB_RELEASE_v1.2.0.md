# Release v1.2.0 - Accurate Payments & Stability Fixes

## 🎯 Major Improvements

### 💰 Accurate Payment Notifications
- **Fixed**: Job completion notifications now show **actual payment amounts** from Nosana dashboard
- **No more calculations**: Direct scraping from dashboard price column
- **100% accuracy**: Payments match exactly what you see on Nosana dashboard

**Before:**
```
Payment: 0.34 NOS (~$0.16 USD) ❌ CALCULATED - WRONG
```

**After:**
```
Payment: $0.176 USD (~0.37 NOS) ✅ FROM DASHBOARD - CORRECT
```

### 🔒 No More Auto-Logout
- **Fixed**: Random session termination issue
- **Root cause**: Missing persistent SECRET_KEY
- **Solution**: Permanent SECRET_KEY ensures tokens survive backend restarts
- **Result**: Reliable, persistent sessions

### ⚡ Server Always Responsive
- **Fixed**: Servers going to sleep after inactivity
- **Solution**: Enhanced keep-alive system (30-second ping)
- **Auto-recovery**: Automatic retry if server sleeping
- **Result**: Always responsive, no delays

---

## 🔔 Enhanced Notifications

### Lock Screen Alerts
Both Firebase Push and Telegram now include:
- ✅ Job duration tracking
- ✅ **Actual payment amounts** (not calculated)
- ✅ HIGH priority delivery
- ✅ Works when phone locked

**Example Notification:**
```
✅ Job Completed
Node X - 55m 8s • $0.176 USD (~0.37 NOS)
```

---

## 🐛 Bug Fixes
- ✅ Fixed incorrect payment calculations in notifications
- ✅ Fixed random auto-logout issues
- ✅ Fixed server sleep causing delayed responses
- ✅ Improved token verification with retry logic
- ✅ Enhanced error handling for network issues

---

## 🚀 What's New
- **Payment Scraping**: Real-time scraping from Nosana dashboard
- **Session Persistence**: Tokens remain valid across restarts
- **Keep-Alive System**: Server never sleeps
- **Smart Retry Logic**: Auto-recovery from network errors
- **Enhanced Monitoring**: Better logging and diagnostics

---

## 📱 PWA Features
- ✅ Auto-update system
- ✅ Lock screen notifications
- ✅ Offline support
- ✅ Install on Android & iOS
- ✅ Native app experience

---

## 🔐 Security
- Persistent SECRET_KEY for JWT tokens
- Enhanced session management
- Rate limiting on all endpoints
- Input validation and XSS protection
- Secure token storage

---

## 📊 Performance
- Health endpoint: < 100ms
- Token verification: < 500ms
- Node status refresh: ~2s per node
- Payment scraping: ~5s (acceptable for accuracy)

---

## 🛠️ Technical Stack
- **Frontend**: React + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **Blockchain**: Solana RPC
- **Notifications**: Firebase FCM + Telegram Bot
- **Web Scraping**: Playwright

---

## 📝 Breaking Changes
**None!** Fully backward compatible.

All existing users automatically benefit from:
- Accurate payment notifications
- No auto-logout issues  
- Better server uptime

---

## 🙏 Credits
Thanks to the Nosana community for feedback and testing!

---

## 📚 Documentation
- Full changelog: [RELEASE_v1.2.0.md](RELEASE_v1.2.0.md)
- Payment fix details: [PAYMENT_NOTIFICATION_FIX.md](PAYMENT_NOTIFICATION_FIX.md)
- System verification: [SYSTEM_VERIFICATION_v1.2.0.md](SYSTEM_VERIFICATION_v1.2.0.md)

---

**Download**: Install as PWA from https://nosanamonitor.preview.emergentagent.com

**Status**: ✅ Production Ready | Stable | All Systems Operational
