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
- **Font**: Space Grotesk for modern tech aesthetic

## 📡 API Endpoints

- `POST /api/nodes` - Add a new node
- `GET /api/nodes` - Get all nodes
- `PUT /api/nodes/{node_id}` - Update node details
- `DELETE /api/nodes/{node_id}` - Delete a node
- `GET /api/nodes/{address}/check-status` - Check single node status from Solana
- `POST /api/nodes/refresh-all-status` - Auto-refresh all nodes from blockchain
- `GET /api/nodes/{address}/dashboard` - Get dashboard link

## 🎯 Your Nodes

Your three nodes are pre-loaded and show **ONLINE** status:
1. **3090 Tuf** - 9DcLW6JkuanvWP2CbKsohChFWGCEiTnAGxA4xdAYHVNq ✅ ONLINE
2. **3090 Palit** - 9hsWPkJUBiDQnc2p7dKi2gMKHp6LwscA6Z5qAF8NGsyV ✅ ONLINE
3. **4090 Gigabyte** - 7Qm8JnTZRs7MbE1hXX3jAEvKfBwv421mRkszBsbfhihH ✅ ONLINE

## 🔥 Achievement Unlocked

**Automated Dashboard with Real Blockchain Data!** 

The app now queries the Solana blockchain directly to fetch your node status, making it a fully automated monitoring solution. No more manual updates needed!
