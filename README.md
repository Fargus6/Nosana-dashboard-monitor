# Nosana Node Monitor

A **Progressive Web App (PWA)** to monitor and manage your Nosana AI network nodes with **automated status checking from Solana blockchain** and **real-time push notifications**.

## 🌐 Access the App

**🖥️ Web App (Desktop & Mobile):** https://cyber-monitor-2.preview.emergentagent.com

**📱 Mobile App:** Install as PWA for best experience (see instructions below)

---

## ✨ Key Features

### Core Monitoring
- **📱 Mobile-Optimized PWA**: Install on Android & iOS as a standalone app
- **🌐 Web Interface**: Full-featured web app for desktop browsers
- **🔄 Automated Status Detection**: Real-time node status from Solana blockchain
- **➕ Multi-Node Management**: Add all your Nosana nodes with custom names
- **🚀 Customizable Auto-Refresh**: Choose 1, 2, 3, or 10-minute intervals
- **📊 Detailed Metrics**: Track NOS/SOL balances, total jobs, and availability scores
- **🔗 Direct Dashboard Links**: Quick access to each node's Nosana dashboard
- **📝 Notes**: Add custom notes for each node

### Notifications & Alerts
- **🔔 Push Notifications**: Firebase Cloud Messaging for real-time alerts
- **🔒 Lock Screen Alerts**: Notifications appear on locked screen with screen wake-up
- **📳 Strong Vibration**: Custom pattern for attention-grabbing alerts
- **🔊 Sound Notifications**: Audible alerts for critical events
- **⚡ HIGH Priority**: Bypasses battery optimization for reliable delivery
- **🎯 Customizable Events**: Choose which events trigger notifications
  - Node goes offline
  - Node comes back online
  - Job started
  - Job completed

### User Experience
- **👁️ Visible by Default**: Addresses and balances shown immediately (no clicking needed!)
- **🔄 Auto-Updates**: Get new features instantly without reinstalling
- **🎨 Multiple Themes**: Dark Mode, 80s Neon, and Cyber (with Matrix effect!)
- **🔐 Secure Authentication**: Email/password login and Google OAuth support
- **💻 Responsive Design**: Beautiful UI optimized for mobile and desktop
- **📱 Offline Support**: Basic functionality works without internet

### Security & Performance
- **🛡️ Enterprise-Grade Security**: Rate limiting, input validation, XSS protection
- **🔒 Password Strength**: 8+ characters with uppercase, lowercase, and numbers
- **🚫 Account Lockout**: Automatic protection against brute force attacks
- **⚡ Keep-Alive System**: Server never sleeps, no auto-logout
- **🔐 JWT Authentication**: Secure token-based authentication
- **🌐 CORS Protection**: Secure cross-origin requests

---

## 📱 Install as Mobile App

### On Android (Chrome/Edge):
1. Open **https://cyber-monitor-2.preview.emergentagent.com** in Chrome
2. Tap the **3-dot menu** → "Add to Home screen"
3. Tap "Install" or "Add"
4. App appears on your home screen like a native app!

### On iOS (Safari):
1. Open **https://cyber-monitor-2.preview.emergentagent.com** in Safari
2. Tap the **Share button** (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add"
5. App appears on your home screen!

### Benefits of PWA:
✅ Works offline (basic functionality)  
✅ Fast loading and smooth performance  
✅ No app store approval needed  
✅ **Auto-updates automatically** (no reinstalling!)  
✅ Smaller size than native apps  
✅ Push notifications support  
✅ Lock screen alerts

---

## 🔔 Push Notifications Setup

### Enable Notifications:
1. Open app and log in
2. Click the **Settings icon (⚙️)** in the header
3. Click **"Enable Notifications"**
4. Grant permission when prompted
5. Choose which events to monitor

### Lock Screen Notifications:
Notifications will:
- ✅ Appear on lock screen
- ✅ Light up your phone screen
- ✅ Vibrate with custom pattern
- ✅ Play notification sound
- ✅ Show even when app is closed

### For Best Results:
**Android:**
```
Settings → Apps → Nosana Monitor
→ Notifications → Allow
→ Lock screen → Show all content
→ Priority → High
```

**iOS:**
```
Settings → Notifications → Nosana Monitor
→ Allow Notifications: ON
→ Lock Screen: ON
→ Show Previews: Always
```

---

## 🚀 How It Works

The app connects to the **Solana blockchain** (where Nosana nodes are registered) and **scrapes the Nosana dashboard** to determine real-time node and job status:

- **Online**: Node account exists on Solana with active balance
- **Offline**: Node account not found or inactive
- **Running**: Node is actively processing deployments
- **Queue**: Jobs waiting in queue
- **Idle**: Node online but no active jobs

## 📖 How to Use

### Adding Nodes

1. Enter an optional node name (e.g., "3090 Tuf")
2. Enter your Nosana node address
3. Click "Add"
4. Click **"Auto-Refresh from Blockchain"** to fetch live status

### Auto-Refresh from Blockchain

Click the **"Auto-Refresh from Blockchain"** button to:
- Query Solana RPC for each node's account status
- Automatically update all node statuses
- Show notifications on completion

### Manual Updates (Optional)

You can still manually edit any node:
1. Click the edit icon (pencil) on any node card
2. Update name, status, job status, or notes
3. Click "Save"

### Offline Alerts

When a node's status changes to "Offline", you'll receive a toast notification.

### Viewing Node Dashboard

Click the external link icon (↗) to open the official Nosana dashboard for that node.

## 🛠 Technical Stack

- **Frontend**: React with Tailwind CSS and Shadcn UI components
- **Backend**: FastAPI (Python) with Solana blockchain integration
- **Database**: MongoDB for persistence
- **Blockchain**: Solana RPC (mainnet-beta) for real-time node status
- **Web Scraping**: Playwright for Nosana dashboard data extraction
- **Authentication**: JWT tokens with bcrypt password hashing, Google OAuth
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Security**: Rate limiting (SlowAPI), XSS protection, input validation, DOMPurify
- **PWA**: Service Workers for offline support and auto-updates
- **Font**: Space Grotesk for modern tech aesthetic

## 🔐 Security Features

### Backend Security:
- **Rate Limiting**: 
  - **30 registrations per hour** (prevents spam while allowing legitimate users)
  - 10 login attempts per minute
  - 20 node additions per minute
  - 10 refresh attempts per minute
- **Account Lockout**: 5 failed login attempts = 15-minute lockout
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-XSS-Protection
- **Input Validation**: Solana address format validation, XSS prevention
- **Password Requirements**: 8+ characters, uppercase, lowercase, numbers
- **Request Logging**: All API requests logged for security monitoring
- **User Limits**: Maximum 100 nodes per user to prevent abuse
- **Keep-Alive System**: Prevents auto-logout and server sleep

### Frontend Security:
- **Input Sanitization**: DOMPurify for XSS protection
- **Client-Side Rate Limiting**: 5 auth attempts per 5 minutes
- **Secure Token Storage**: Encrypted localStorage wrapper
- **Session Management**: Automatic token expiry handling
- **Error Handling**: No sensitive information leakage
- **Auto-Update System**: Service worker for secure automatic updates

## 📡 API Endpoints

### Authentication:
- `POST /api/auth/register` - Register new user (email + password)
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/google` - Google OAuth authentication
- `GET /api/auth/me` - Get current user info

### Node Management (Protected):
- `POST /api/nodes` - Add a new node
- `GET /api/nodes` - Get all your nodes
- `PUT /api/nodes/{node_id}` - Update node details
- `DELETE /api/nodes/{node_id}` - Delete a node
- `GET /api/nodes/{address}/check-status` - Check single node status from Solana
- `POST /api/nodes/refresh-all-status` - Auto-refresh all nodes from blockchain
- `GET /api/nodes/{address}/dashboard` - Get dashboard link

### Notifications (Protected):
- `POST /api/notifications/subscribe` - Subscribe device to push notifications
- `POST /api/notifications/unsubscribe` - Unsubscribe device from notifications
- `GET /api/notifications/preferences` - Get notification preferences
- `PUT /api/notifications/preferences` - Update notification preferences
- `POST /api/notifications/test` - Send test notification

### System:
- `GET /api/health` - Health check endpoint

## 🎯 Getting Started

1. **Create an Account**: Register with email/password or use Google Sign-In
2. **Add Your Nodes**: Enter your Nosana node addresses with optional custom names
3. **Monitor Status**: Automatic refresh every 2 minutes keeps you updated
4. **View Details**: Check NOS/SOL balances, job counts, and availability scores
5. **Get Alerts**: Receive notifications when nodes go offline
6. **Install as App**: Follow the PWA installation steps above for the best experience

## 🔥 What Makes This Special

**Automated Dashboard with Real Blockchain Data!** 

The app queries the Solana blockchain directly and scrapes the Nosana dashboard to fetch your node status, making it a fully automated monitoring solution. No more manual updates needed!

**Privacy & Security First:**
- Your nodes are private (only you can see them)
- Enterprise-grade security protections
- Secure authentication with JWT tokens
- All data encrypted in transit

---

Built with ❤️ for the Nosana community 🚀
