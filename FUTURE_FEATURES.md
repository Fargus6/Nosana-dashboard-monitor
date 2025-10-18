# 🚀 Future Features & Enhancements

## 📱 Push Notifications via Firebase FCM (IN PROGRESS - NEXT)

**Status:** Ready to implement - waiting for Firebase credentials

**User Requirements:**
- ✅ Firebase Cloud Messaging (FCM) - better iOS support
- ✅ Choosable event triggers (offline, online, job started, job completed)
- ✅ Vibration on notifications
- ✅ Sound toggle
- ✅ Real-time updates
- ✅ Auto-refresh intervals: 1, 2, 3, 10 minutes selector

**Firebase Setup Steps for User:**
1. Create Firebase project at https://console.firebase.google.com/
2. Enable Cloud Messaging
3. Add web app
4. Generate VAPID key

**Credentials Needed:**
```
From "General" tab:
- API Key: AIza...
- Project ID: your-project-123
- App ID: 1:123456789:web:abc123...

From "Cloud Messaging" tab:
- Sender ID: 123456789
- Server Key (backend): AAAA...xxx
- VAPID Key: BN7x...
```

**Implementation Plan:**

**Backend:**
- Install `firebase-admin` for Python
- Store FCM device tokens in database (per user)
- API endpoints:
  - `POST /api/notifications/register` - Register device token
  - `POST /api/notifications/preferences` - Save user preferences
  - `GET /api/notifications/preferences` - Get user preferences
- Background job to detect node status changes and send notifications
- Rate limiting: max 100 notifications per user per day

**Frontend:**
- Install `firebase` npm package
- Request notification permission on login
- Settings page with toggles:
  - Node goes offline ✓
  - Node comes online ✓
  - Job started (running) ✓
  - Job completed (idle) ✓
  - Vibration on/off
  - Sound on/off
  - Do Not Disturb hours
- Auto-refresh interval dropdown (1, 2, 3, 10 min)
- Test notification button
- Firebase service worker for background notifications

**Features to Add:**
- Notification history/log
- Mute specific nodes
- Smart batching (multiple events = single notification)
- Notification analytics

---

## 🔄 Remote Node Restart (HIGH PRIORITY)

**Feature Description:**
Add ability to remotely restart Nosana nodes directly from the app via SSH connection.

**Requirements Needed:**
1. **Server Connection Details**
   - IP Address or Hostname for each server
   - SSH Port (usually 22)
   - SSH Username

2. **SSH Authentication Method**
   - Option A: SSH Private Key (Recommended)
   - Option B: Password

3. **Exact Restart Command**
   - The exact command to restart Nosana (e.g., `nosana start`, `systemctl restart nosana`, etc.)

4. **Node-to-Server Mapping**
   - Which node addresses are on which servers

5. **Sudo Requirements**
   - Does the restart command need `sudo`?
   - Is passwordless sudo enabled?

**Implementation Plan:**
- Backend: Python `paramiko` library for SSH
- Encrypted credential storage in database
- API endpoint: `POST /api/nodes/{node_id}/restart`
- Frontend: Restart button (⟳) on each node card
- Confirmation dialog before restart
- Rate limiting: 5 restarts per hour per node
- Audit logging of all restart attempts

**Additional Commands to Consider:**
- Stop node
- Check node logs
- View detailed node status
- Update node software

---

## 📝 Other Future Ideas

### Notifications & Alerts
- Email alerts when nodes go offline
- Discord/Telegram webhook notifications
- Custom alert thresholds

### Analytics & Reporting
- Historical uptime tracking
- Job completion statistics
- Revenue/earnings tracking
- Performance graphs and charts

### Multi-User Features
- Team collaboration (share node access)
- Role-based permissions
- Organization/group management

### Advanced Monitoring
- CPU/Memory/Disk usage monitoring
- Network bandwidth tracking
- Temperature monitoring
- Predictive maintenance alerts

### Automation
- Auto-restart on failure
- Scheduled maintenance windows
- Automatic updates
- Load balancing across nodes

---

*Last Updated: October 2024*
