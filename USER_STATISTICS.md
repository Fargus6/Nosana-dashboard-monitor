# 👥 User Statistics - Nosana Node Monitor

## Current Status

**Date**: October 18, 2024  
**Database**: MongoDB (nosana_monitor)  
**Status**: No users registered yet ⚠️

---

## What User Metrics Are Tracked

When users start using the application, the following statistics will be available:

### 📊 User Overview
- **Total Registered Users** - Count of all registered accounts
- **New Users Today** - Daily registration count
- **Active Users** - Users who have added nodes
- **Inactive Users** - Registered but no nodes added

### 🔐 Authentication Breakdown
- **Email/Password Users** - Traditional registration
- **Google OAuth Users** - Social login users
- **Authentication Method Split** - Percentage breakdown

### 📅 Registration Timeline
- **Users by Date** - Registration history
- **Growth Trend** - Daily/weekly/monthly growth
- **Peak Registration Days** - Busiest signup periods

### 🖥️ Node Statistics
- **Total Nodes Monitored** - All nodes across all users
- **Users with Nodes** - Active monitoring users
- **Users without Nodes** - Registered but not monitoring
- **Average Nodes per User** - Mean node count
- **Max Nodes (Single User)** - Highest node count
- **Min Nodes (Active Users)** - Lowest active node count

### 📡 Node Status Distribution
- **Online Nodes** - Currently online and responding
- **Offline Nodes** - Not responding
- **Unknown Status** - Status not yet determined

### 💼 Job Status Breakdown
- **Idle Nodes** - No active jobs
- **Queue Nodes** - Jobs queued
- **Running Nodes** - Actively processing jobs

### 🔔 Notification Engagement
- **Total Device Tokens** - Registered notification devices
- **Users with Notifications** - Enabled push notifications
- **Users without Notifications** - Not opted in
- **Average Devices per User** - Multiple device support

### ⚙️ Notification Preferences
- **Node Online Alerts** - Users subscribed
- **Node Offline Alerts** - Users subscribed
- **Job Started Alerts** - Users subscribed
- **Job Completed Alerts** - Users subscribed
- **Sound Enabled** - Audio notification preference
- **Vibration Enabled** - Haptic feedback preference

### 📈 Engagement Metrics
- **Activation Rate** - % of users who added nodes
- **Engagement Rate** - % of users with notifications enabled
- **Retention Rate** - Users still active after 30 days
- **Power User Rate** - Users with 10+ nodes

### 🏆 User Cohorts
- **Power Users** - 10+ nodes monitored
- **Regular Users** - 1-9 nodes monitored
- **Inactive Users** - 0 nodes (registered only)

### 🎯 Top Users
- **By Node Count** - Users monitoring most nodes
- **By Engagement** - Most active users
- **Early Adopters** - First registered users

---

## Sample Statistics (Once Users Register)

### Example Output:

```
================================================================================
👥 USER STATISTICS - NOSANA NODE MONITOR
================================================================================

📊 OVERVIEW
--------------------------------------------------------------------------------
Total Registered Users:    127

🔐 AUTHENTICATION
--------------------------------------------------------------------------------
Email/Password Users:      89 (70.1%)
Google OAuth Users:        38 (29.9%)

📅 REGISTRATION TIMELINE
--------------------------------------------------------------------------------
  2024-09-15:  5 user(s)
  2024-09-16:  12 user(s)
  2024-09-17:  8 user(s)
  2024-09-18:  15 user(s)
  2024-09-19:  23 user(s)
  ... (continues)

🖥️  NODE STATISTICS
--------------------------------------------------------------------------------
Total Nodes Monitored:     543
Users with Nodes:          98 (77.2%)
Users without Nodes:       29 (22.8%)
Average Nodes/User:        4.3
Max Nodes (single user):   47
Min Nodes (active users):  1

📡 NODE STATUS BREAKDOWN
--------------------------------------------------------------------------------
  Online               412 nodes (75.9%)
  Offline              98 nodes (18.0%)
  Unknown              33 nodes (6.1%)

💼 JOB STATUS BREAKDOWN
--------------------------------------------------------------------------------
  Idle                 324 nodes (59.7%)
  Queue                87 nodes (16.0%)
  Running              132 nodes (24.3%)

🔔 NOTIFICATION STATISTICS
--------------------------------------------------------------------------------
Total Device Tokens:       156
Users with Notifications:  73 (57.5%)
Users without Notifications: 54 (42.5%)
Avg Devices per User:      2.1

⚙️  NOTIFICATION PREFERENCES
--------------------------------------------------------------------------------
Node Online Alerts:        68 users
Node Offline Alerts:       71 users
Job Started Alerts:        65 users
Job Completed Alerts:      62 users
Sound Enabled:             69 users
Vibration Enabled:         70 users

📈 ENGAGEMENT METRICS
--------------------------------------------------------------------------------
Activation Rate:           77.2% (users with nodes)
Engagement Rate:           57.5% (users with notifications)

🏆 TOP USERS (by node count)
--------------------------------------------------------------------------------
  1. joh***@example.com              47 nodes
  2. sar***@gmail.com                32 nodes
  3. mik***@company.com              28 nodes
  4. ann***@email.com                24 nodes
  5. rob***@domain.com               19 nodes

👥 USER COHORTS
--------------------------------------------------------------------------------
Power Users (10+ nodes):   15 (11.8%)
Regular Users (1-9 nodes): 83 (65.4%)
Inactive Users (0 nodes):  29 (22.8%)

📊 SUMMARY
--------------------------------------------------------------------------------
Total Users:               127
Total Nodes:               543
Total Device Tokens:       156
Activation Rate:           77.2%
Engagement Rate:           57.5%
Avg Nodes per User:        4.3
```

---

## How to Get User Statistics

### Real-Time Statistics:
```bash
# Run on server
cd /app/backend
python3 /tmp/user_stats.py
```

### Database Queries:

#### Total Users
```javascript
db.users.countDocuments({})
```

#### Users by Registration Date
```javascript
db.users.aggregate([
  {
    $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
      count: { $sum: 1 }
    }
  },
  { $sort: { _id: 1 } }
])
```

#### Users with Nodes
```javascript
db.nodes.aggregate([
  { $group: { _id: "$user_id", nodeCount: { $sum: 1 } } },
  { $match: { nodeCount: { $gt: 0 } } },
  { $count: "usersWithNodes" }
])
```

#### Notification Engagement
```javascript
db.device_tokens.aggregate([
  { $group: { _id: "$user_id" } },
  { $count: "usersWithNotifications" }
])
```

---

## Privacy & Security

### User Data Protection:
- ✓ Email addresses are masked in statistics (joh***@example.com)
- ✓ No personal information exposed in logs
- ✓ Passwords are hashed (bcrypt)
- ✓ JWT tokens are short-lived (7 days)
- ✓ Device tokens are encrypted
- ✓ User IDs are UUIDs (not sequential)

### Data Retention:
- **User Accounts**: Indefinite (until deletion request)
- **Nodes**: Until user deletes
- **Device Tokens**: Until unregistered
- **Notification Preferences**: Until user changes
- **Session Tokens**: 7 days expiry

### GDPR Compliance:
- Users can delete their account
- Users can export their data
- Users can disable notifications
- Clear privacy policy
- Consent for data collection

---

## Key Performance Indicators (KPIs)

### User Growth KPIs:
- **Daily Active Users (DAU)** - Users who refresh nodes
- **Monthly Active Users (MAU)** - Users active in last 30 days
- **User Growth Rate** - % increase in registrations
- **Churn Rate** - % of users who stop using app

### Engagement KPIs:
- **Activation Rate** - % users who add nodes (Target: > 70%)
- **Engagement Rate** - % users with notifications (Target: > 50%)
- **Retention Rate** - % users still active after 30 days (Target: > 60%)
- **Power User Rate** - % users with 10+ nodes (Target: > 10%)

### Feature Adoption KPIs:
- **Notification Adoption** - % enabling push notifications
- **Multi-Node Users** - % users with 2+ nodes
- **OAuth Adoption** - % using Google login
- **PWA Install Rate** - % adding to home screen

### Health Metrics:
- **Node Health** - % nodes online
- **Job Success Rate** - % jobs completing successfully
- **Notification Delivery** - % notifications delivered
- **API Success Rate** - % API calls successful

---

## User Lifecycle

### Stage 1: Registration
- User signs up (email or Google)
- Account created in database
- **Metric**: Total Users

### Stage 2: Activation
- User adds first node
- Status monitoring begins
- **Metric**: Activation Rate

### Stage 3: Engagement
- User enables notifications
- Configures preferences
- **Metric**: Engagement Rate

### Stage 4: Growth
- User adds more nodes
- Uses multiple devices
- **Metric**: Nodes per User

### Stage 5: Retention
- User continues monitoring
- Regular app usage
- **Metric**: Retention Rate

---

## Current State

### Database Collections:

| Collection | Documents | Status |
|------------|-----------|--------|
| `users` | 0 | ⚠️ Empty |
| `nodes` | 0 | ⚠️ Empty |
| `device_tokens` | 0 | ⚠️ Empty |
| `notification_preferences` | 0 | ⚠️ Empty |

### Next Steps to See Statistics:

1. **Register Users**
   - Go to: https://alert-hub-11.preview.emergentagent.com
   - Create accounts (email or Google)

2. **Add Nodes**
   - Add Solana wallet addresses
   - Monitor node status

3. **Enable Notifications**
   - Set up push notifications
   - Configure preferences

4. **Run Statistics Script**
   - Execute: `python3 /tmp/user_stats.py`
   - View detailed breakdown

---

## Monitoring Tools

### Built-in Statistics:
- User count: `db.users.countDocuments({})`
- Node count: `db.nodes.countDocuments({})`
- Token count: `db.device_tokens.countDocuments({})`

### Custom Reports:
- Generate with Python script
- Export to CSV/JSON
- Visualize with charts

### Real-time Dashboard (Future):
- User growth charts
- Node status visualization
- Engagement heatmaps
- Geographic distribution

---

## Data Export

### Export User Statistics:
```bash
# Export to JSON
mongoexport --db=nosana_monitor --collection=users --out=users.json

# Export to CSV
mongoexport --db=nosana_monitor --collection=users --type=csv --fields=id,email,created_at --out=users.csv
```

### Anonymized Statistics:
```python
# Get anonymized statistics
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def export_stats():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.nosana_monitor
    
    stats = {
        'total_users': await db.users.count_documents({}),
        'total_nodes': await db.nodes.count_documents({}),
        'total_tokens': await db.device_tokens.count_documents({}),
        'avg_nodes_per_user': ... # Calculate average
    }
    
    return stats
```

---

## Summary

**Current Status**: 🟡 **Waiting for Users**

Once users start registering and using the app, comprehensive statistics will be available including:
- User demographics
- Engagement metrics
- Node statistics
- Notification adoption
- Feature usage
- Growth trends

**Check Statistics**: Run `python3 /tmp/user_stats.py` anytime to see current data.

---

**Last Updated**: October 18, 2024  
**Database**: MongoDB (nosana_monitor)  
**App URL**: https://alert-hub-11.preview.emergentagent.com
