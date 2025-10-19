#!/usr/bin/env python3
"""
Generate comprehensive statistics for Nosana Node Monitor app
"""
import asyncio
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
from collections import defaultdict

# MongoDB connection
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')

async def get_app_statistics():
    """Generate comprehensive app statistics"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"\n{'='*100}")
    print(f"NOSANA NODE MONITOR - APP STATISTICS")
    print(f"{'='*100}")
    print(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # ==================== USER STATISTICS ====================
    print(f"{'='*100}")
    print(f"👥 USER STATISTICS")
    print(f"{'='*100}\n")
    
    # Total users
    total_users = await db.users.count_documents({})
    print(f"Total Registered Users: {total_users}")
    
    # Users by auth method
    google_users = await db.users.count_documents({"google_id": {"$exists": True}})
    email_users = total_users - google_users
    print(f"   • Email/Password: {email_users}")
    print(f"   • Google OAuth: {google_users}")
    
    # Users with Telegram linked
    telegram_users = await db.telegram_users.count_documents({})
    print(f"\nTelegram Integration:")
    print(f"   • Users with Telegram linked: {telegram_users}")
    print(f"   • Telegram adoption rate: {(telegram_users/total_users*100) if total_users > 0 else 0:.1f}%")
    
    # Users with notifications enabled
    notifications_enabled = await db.device_tokens.distinct("user_id")
    print(f"\nPush Notifications:")
    print(f"   • Users with push enabled: {len(notifications_enabled)}")
    print(f"   • Push adoption rate: {(len(notifications_enabled)/total_users*100) if total_users > 0 else 0:.1f}%")
    
    # ==================== NODE STATISTICS ====================
    print(f"\n{'='*100}")
    print(f"🖥️  NODE STATISTICS")
    print(f"{'='*100}\n")
    
    # Total nodes
    total_nodes = await db.nodes.count_documents({})
    print(f"Total Nodes Monitored: {total_nodes}")
    
    # Nodes per user
    if total_users > 0:
        avg_nodes_per_user = total_nodes / total_users
        print(f"Average Nodes per User: {avg_nodes_per_user:.1f}")
    
    # Node status breakdown
    online_nodes = await db.nodes.count_documents({"status": "online"})
    offline_nodes = await db.nodes.count_documents({"status": "offline"})
    unknown_nodes = total_nodes - online_nodes - offline_nodes
    
    print(f"\nNode Status:")
    print(f"   • Online: {online_nodes} ({(online_nodes/total_nodes*100) if total_nodes > 0 else 0:.1f}%)")
    print(f"   • Offline: {offline_nodes} ({(offline_nodes/total_nodes*100) if total_nodes > 0 else 0:.1f}%)")
    print(f"   • Unknown: {unknown_nodes} ({(unknown_nodes/total_nodes*100) if total_nodes > 0 else 0:.1f}%)")
    
    # Job status breakdown
    running_jobs = await db.nodes.count_documents({"job_status": "running"})
    idle_jobs = await db.nodes.count_documents({"job_status": "idle"})
    queue_jobs = await db.nodes.count_documents({"job_status": "queue"})
    
    print(f"\nJob Status:")
    print(f"   • Running: {running_jobs}")
    print(f"   • Queue: {queue_jobs}")
    print(f"   • Idle: {idle_jobs}")
    
    # Top users by node count
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_users = await db.nodes.aggregate(pipeline).to_list(5)
    
    if top_users:
        print(f"\nTop Users by Node Count:")
        for i, user in enumerate(top_users, 1):
            print(f"   {i}. User {user['_id'][:8]}...: {user['count']} nodes")
    
    # ==================== ACTIVITY STATISTICS ====================
    print(f"\n{'='*100}")
    print(f"📊 ACTIVITY STATISTICS")
    print(f"{'='*100}\n")
    
    # Recent activity (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # New users (last 7 days)
    recent_users = await db.users.count_documents({
        "created_at": {"$gte": seven_days_ago.isoformat()}
    })
    print(f"Last 7 Days:")
    print(f"   • New users: {recent_users}")
    
    # New nodes (last 7 days)
    recent_nodes = await db.nodes.count_documents({
        "created_at": {"$gte": seven_days_ago.isoformat()}
    })
    print(f"   • New nodes added: {recent_nodes}")
    
    # ==================== NOTIFICATION STATISTICS ====================
    print(f"\n{'='*100}")
    print(f"🔔 NOTIFICATION STATISTICS")
    print(f"{'='*100}\n")
    
    # Device tokens (unique devices)
    total_devices = await db.device_tokens.count_documents({})
    print(f"Registered Devices: {total_devices}")
    
    # Notification preferences
    users_with_prefs = await db.notification_preferences.count_documents({})
    print(f"Users with Custom Preferences: {users_with_prefs}")
    
    # Count users with each notification type enabled
    prefs = await db.notification_preferences.find({}).to_list(None)
    notification_stats = {
        'offline': 0,
        'online': 0,
        'job_started': 0,
        'job_completed': 0,
        'low_balance': 0
    }
    
    for pref in prefs:
        if pref.get('notify_offline', True):
            notification_stats['offline'] += 1
        if pref.get('notify_online', True):
            notification_stats['online'] += 1
        if pref.get('notify_job_started', True):
            notification_stats['job_started'] += 1
        if pref.get('notify_job_completed', True):
            notification_stats['job_completed'] += 1
        if pref.get('notify_low_balance', True):
            notification_stats['low_balance'] += 1
    
    if users_with_prefs > 0:
        print(f"\nNotification Types Enabled:")
        print(f"   • Node Offline: {notification_stats['offline']} ({(notification_stats['offline']/users_with_prefs*100):.1f}%)")
        print(f"   • Node Online: {notification_stats['online']} ({(notification_stats['online']/users_with_prefs*100):.1f}%)")
        print(f"   • Job Started: {notification_stats['job_started']} ({(notification_stats['job_started']/users_with_prefs*100):.1f}%)")
        print(f"   • Job Completed: {notification_stats['job_completed']} ({(notification_stats['job_completed']/users_with_prefs*100):.1f}%)")
        print(f"   • Low Balance: {notification_stats['low_balance']} ({(notification_stats['low_balance']/users_with_prefs*100):.1f}%)")
    
    # ==================== BALANCE STATISTICS ====================
    print(f"\n{'='*100}")
    print(f"💰 BALANCE STATISTICS")
    print(f"{'='*100}\n")
    
    # Get all nodes with balances
    nodes_with_balances = await db.nodes.find({
        "$or": [
            {"nos_balance": {"$exists": True, "$ne": None}},
            {"sol_balance": {"$exists": True, "$ne": None}}
        ]
    }).to_list(None)
    
    total_nos = 0
    total_sol = 0
    nodes_with_nos = 0
    nodes_with_sol = 0
    low_sol_count = 0
    
    for node in nodes_with_balances:
        if node.get('nos_balance'):
            total_nos += node['nos_balance']
            nodes_with_nos += 1
        if node.get('sol_balance'):
            total_sol += node['sol_balance']
            nodes_with_sol += 1
            if node['sol_balance'] < 0.006:
                low_sol_count += 1
    
    print(f"Total Monitored Balances:")
    print(f"   • Total NOS: {total_nos:.2f} NOS")
    print(f"   • Total SOL: {total_sol:.6f} SOL")
    print(f"\nNodes with Balance Data:")
    print(f"   • With NOS balance: {nodes_with_nos}")
    print(f"   • With SOL balance: {nodes_with_sol}")
    
    if nodes_with_nos > 0:
        avg_nos = total_nos / nodes_with_nos
        print(f"\nAverage per Node:")
        print(f"   • NOS: {avg_nos:.2f}")
    
    if nodes_with_sol > 0:
        avg_sol = total_sol / nodes_with_sol
        print(f"   • SOL: {avg_sol:.6f}")
    
    print(f"\nLow Balance Alerts:")
    print(f"   • Nodes with SOL < 0.006: {low_sol_count}")
    
    # ==================== EARNINGS STATISTICS ====================
    print(f"\n{'='*100}")
    print(f"📈 EARNINGS TRACKING")
    print(f"{'='*100}\n")
    
    # Check if earnings collection exists
    earnings_count = await db.job_earnings.count_documents({})
    if earnings_count > 0:
        print(f"Total Job Earnings Recorded: {earnings_count}")
        
        # Sum total earnings
        pipeline = [
            {"$group": {
                "_id": None,
                "total_usd": {"$sum": "$usd_value"},
                "total_nos": {"$sum": "$nos_earned"},
                "total_duration": {"$sum": "$duration_seconds"}
            }}
        ]
        earnings_sum = await db.job_earnings.aggregate(pipeline).to_list(1)
        
        if earnings_sum:
            total = earnings_sum[0]
            print(f"   • Total USD Earned: ${total['total_usd']:.2f}")
            print(f"   • Total NOS Earned: {total['total_nos']:.2f} NOS")
            
            total_hours = total['total_duration'] / 3600
            print(f"   • Total Job Time: {total_hours:.1f} hours")
            
            if total_hours > 0:
                avg_hourly = total['total_usd'] / total_hours
                print(f"   • Average Hourly Rate: ${avg_hourly:.2f}/hour")
    else:
        print(f"No earnings data recorded yet")
    
    # ==================== SYSTEM HEALTH ====================
    print(f"\n{'='*100}")
    print(f"🔧 SYSTEM HEALTH")
    print(f"{'='*100}\n")
    
    # Collection sizes
    collections = ['users', 'nodes', 'device_tokens', 'telegram_users', 'notification_preferences', 'job_earnings']
    print(f"Database Collections:")
    for collection in collections:
        count = await db[collection].count_documents({})
        print(f"   • {collection}: {count} documents")
    
    # Recent updates
    recently_updated = await db.nodes.count_documents({
        "updated_at": {"$gte": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()}
    })
    print(f"\nRecent Activity:")
    print(f"   • Nodes updated in last hour: {recently_updated}")
    
    print(f"\n{'='*100}")
    print(f"✅ Statistics Generated Successfully")
    print(f"{'='*100}\n")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(get_app_statistics())
