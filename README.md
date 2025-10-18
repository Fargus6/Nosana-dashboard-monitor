# Nosana Node Monitor

A **Progressive Web App (PWA)** to monitor and manage your Nosana AI network nodes with **automated status checking from Solana blockchain**.

## ✨ Key Features

- **📱 Mobile-Optimized PWA**: Install on Android & iOS as a standalone app
- **🔄 Automated Status Detection**: Real-time node status from Solana blockchain
- **➕ Multi-Node Management**: Add all your Nosana nodes with custom names
- **🚀 One-Click Auto-Refresh**: Fetch live status for all nodes from blockchain (every 2 minutes)
- **📊 Detailed Metrics**: Track NOS/SOL balances, total jobs, and availability scores
- **🔔 Offline Alerts**: Toast notifications when nodes go offline
- **👁️ Privacy Toggle**: Show/hide node addresses and financial details with eye icon
- **🔐 Secure Authentication**: Email/password login and Google OAuth support
- **🛡️ Enterprise-Grade Security**: Rate limiting, input validation, XSS protection
- **🎨 Dual Themes**: Modern Blue and Nosana-inspired 80s Neon themes
- **📝 Notes**: Add custom notes for each node
- **🔗 Direct Dashboard Links**: Quick access to each node's Nosana dashboard
- **💻 Responsive Design**: Beautiful UI optimized for mobile and desktop

## 📱 Install as Mobile App

### On Android (Chrome/Edge):
1. Open **https://ai-node-tracker.preview.emergentagent.com** in Chrome
2. Tap the **3-dot menu** → "Add to Home screen"
3. Tap "Install" or "Add"
4. App appears on your home screen like a native app!

### On iOS (Safari):
1. Open **https://ai-node-tracker.preview.emergentagent.com** in Safari
2. Tap the **Share button** (square with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add"
5. App appears on your home screen!

### Benefits of PWA:
✅ Works offline (basic functionality)  
✅ Fast loading and smooth performance  
✅ No app store approval needed  
✅ Auto-updates when you refresh  
✅ Smaller size than native apps

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
- **Authentication**: JWT tokens with bcrypt password hashing
- **Security**: Rate limiting, XSS protection, input validation, DOMPurify
- **Font**: Space Grotesk for modern tech aesthetic

## 🔐 Security Features

### Backend Security:
- **Rate Limiting**: 
  - 5 registrations per hour
  - 10 login attempts per minute
  - 20 node additions per minute
- **Account Lockout**: 5 failed login attempts = 15-minute lockout
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-XSS-Protection
- **Input Validation**: Solana address format validation, XSS prevention
- **Password Requirements**: 8+ characters, uppercase, lowercase, numbers
- **Request Logging**: All API requests logged for security monitoring
- **User Limits**: Maximum 100 nodes per user to prevent abuse

### Frontend Security:
- **Input Sanitization**: DOMPurify for XSS protection
- **Client-Side Rate Limiting**: 5 auth attempts per 5 minutes
- **Secure Token Storage**: Encrypted localStorage wrapper
- **Session Management**: Automatic token expiry handling
- **Error Handling**: No sensitive information leakage

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
