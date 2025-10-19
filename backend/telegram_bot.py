import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize MongoDB
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

# Initialize Bot
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

bot = Bot(token=TELEGRAM_TOKEN)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Link Telegram to user account"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    logger.info(f"Start command from chat_id: {chat_id}, user: {user.username}")
    
    # Generate unique linking code
    import secrets
    link_code = secrets.token_hex(4).upper()
    
    # Store linking code in database
    await db.telegram_link_codes.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "chat_id": chat_id,
                "link_code": link_code,
                "username": user.username,
                "first_name": user.first_name,
                "created_at": asyncio.get_event_loop().time()
            }
        },
        upsert=True
    )
    
    welcome_message = f"""
🤖 **Welcome to Nosana Node Monitor Bot!**

To link your account:

1️⃣ Open the web app: https://nosana-monitor.preview.emergentagent.com
2️⃣ Go to Settings ⚙️
3️⃣ Find "Telegram Notifications" section
4️⃣ Enter this code: `{link_code}`

Once linked, you'll receive instant alerts:
• 🔴 Node goes offline
• 🟡 Low SOL balance (< 0.006)
• ✅ Node back online

**Commands:**
/status - Check all nodes
/nodes - List nodes with details
/balance - View SOL/NOS balances
/help - Show commands
"""
    
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - Show all node statuses"""
    chat_id = update.effective_chat.id
    
    # Find linked user
    telegram_user = await db.telegram_users.find_one({"chat_id": chat_id})
    
    if not telegram_user:
        await update.message.reply_text(
            "❌ Not linked! Use /start to link your account first."
        )
        return
    
    user_id = telegram_user['user_id']
    
    # Get user's nodes
    nodes = await db.nodes.find({"user_id": user_id}).to_list(100)
    
    if not nodes:
        await update.message.reply_text("📭 No nodes found. Add nodes in the web app!")
        return
    
    # Count statuses
    online = sum(1 for n in nodes if n.get('status') == 'online')
    offline = sum(1 for n in nodes if n.get('status') == 'offline')
    unknown = len(nodes) - online - offline
    
    status_message = f"""
📊 **Node Status Summary**

Total Nodes: {len(nodes)}
✅ Online: {online}
❌ Offline: {offline}
❓ Unknown: {unknown}

Use /nodes for detailed list
"""
    
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)


async def nodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /nodes command - List all nodes with details"""
    chat_id = update.effective_chat.id
    
    # Find linked user
    telegram_user = await db.telegram_users.find_one({"chat_id": chat_id})
    
    if not telegram_user:
        await update.message.reply_text(
            "❌ Not linked! Use /start to link your account first."
        )
        return
    
    user_id = telegram_user['user_id']
    
    # Get user's nodes
    nodes_list = await db.nodes.find({"user_id": user_id}).to_list(100)
    
    if not nodes_list:
        await update.message.reply_text("📭 No nodes found. Add nodes in the web app!")
        return
    
    nodes_message = "🖥️ **Your Nodes:**\n\n"
    
    for i, node in enumerate(nodes_list, 1):
        name = node.get('name', 'Unnamed')
        address = node.get('address', '')
        status_emoji = "✅" if node.get('status') == 'online' else "❌" if node.get('status') == 'offline' else "❓"
        status = node.get('status', 'unknown').upper()
        job_status = node.get('job_status', 'idle').upper()
        
        nodes_message += f"{i}. **{name}**\n"
        nodes_message += f"   {status_emoji} Status: {status}\n"
        nodes_message += f"   💼 Job: {job_status}\n"
        nodes_message += f"   📍 {address[:8]}...{address[-8:]}\n\n"
    
    nodes_message += "_Use /balance for SOL/NOS info_"
    
    # Split message if too long
    if len(nodes_message) > 4096:
        # Send in chunks
        for i in range(0, len(nodes_message), 4000):
            await update.message.reply_text(
                nodes_message[i:i+4000],
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await update.message.reply_text(nodes_message, parse_mode=ParseMode.MARKDOWN)


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command - Show SOL/NOS balances"""
    chat_id = update.effective_chat.id
    
    # Find linked user
    telegram_user = await db.telegram_users.find_one({"chat_id": chat_id})
    
    if not telegram_user:
        await update.message.reply_text(
            "❌ Not linked! Use /start to link your account first."
        )
        return
    
    user_id = telegram_user['user_id']
    
    # Get user's nodes
    nodes_list = await db.nodes.find({"user_id": user_id}).to_list(100)
    
    if not nodes_list:
        await update.message.reply_text("📭 No nodes found.")
        return
    
    balance_message = "💰 **Balance Report:**\n\n"
    
    total_sol = 0.0
    total_nos = 0.0
    low_balance_nodes = []
    
    for node in nodes_list:
        name = node.get('name', 'Unnamed')
        sol = node.get('sol_balance') or 0.0
        nos = node.get('nos_balance') or 0.0
        
        total_sol += sol
        total_nos += nos
        
        # Check for low balance
        if sol < 0.006 and sol > 0:
            low_balance_nodes.append((name, sol))
        
        balance_message += f"**{name}**\n"
        balance_message += f"   SOL: {sol:.6f}\n"
        balance_message += f"   NOS: {nos:.2f}\n\n"
    
    balance_message += f"**Totals:**\n"
    balance_message += f"🔹 Total SOL: {total_sol:.6f}\n"
    balance_message += f"🔹 Total NOS: {total_nos:.2f}\n"
    
    if low_balance_nodes:
        balance_message += f"\n⚠️ **Low Balance Warnings:**\n"
        for name, sol in low_balance_nodes:
            balance_message += f"• {name}: {sol:.6f} SOL (< 0.006)\n"
    
    # Split message if too long
    if len(balance_message) > 4096:
        for i in range(0, len(balance_message), 4000):
            await update.message.reply_text(
                balance_message[i:i+4000],
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await update.message.reply_text(balance_message, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🤖 **Nosana Node Monitor Bot**

**Commands:**
/start - Link your account
/status - Quick status summary
/nodes - Detailed node list
/balance - SOL/NOS balances
/help - Show this message

**Automatic Alerts:**
You'll receive instant notifications for:
• 🔴 Node goes offline
• 🟡 Low SOL balance (< 0.006)
• ✅ Node back online

**Web App:**
https://nosana-monitor.preview.emergentagent.com

Need help? Check the web app settings!
"""
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


# Helper function to send notifications
async def send_telegram_notification(chat_id: int, message: str, parse_mode: str = ParseMode.MARKDOWN):
    """Send notification to user"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode
        )
        logger.info(f"Notification sent to chat_id: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification to chat_id {chat_id}: {str(e)}")
        return False


# Alert functions
async def send_node_offline_alert(user_id: str, node_name: str, node_address: str):
    """Send alert when node goes offline"""
    telegram_user = await db.telegram_users.find_one({"user_id": user_id})
    
    if not telegram_user:
        return
    
    chat_id = telegram_user['chat_id']
    
    message = f"""
🔴 **NODE OFFLINE ALERT**

Node: **{node_name}**
Address: `{node_address[:8]}...{node_address[-8:]}`

❗ Your node is currently offline.

[View Dashboard](https://dashboard.nosana.com/host/{node_address})
"""
    
    await send_telegram_notification(chat_id, message)


async def send_low_balance_alert(user_id: str, node_name: str, node_address: str, sol_balance: float):
    """Send alert when SOL balance is critically low"""
    telegram_user = await db.telegram_users.find_one({"user_id": user_id})
    
    if not telegram_user:
        return
    
    chat_id = telegram_user['chat_id']
    
    message = f"""
🟡 **CRITICAL: LOW SOL BALANCE**

Node: **{node_name}**
Address: `{node_address[:8]}...{node_address[-8:]}`

Current Balance: **{sol_balance:.6f} SOL**
Minimum Required: **0.005 SOL**

⚠️ **Action Required:** Top up immediately!
Your node may stop accepting jobs.

[How to Top Up](https://docs.nosana.io)
"""
    
    await send_telegram_notification(chat_id, message)


async def send_node_online_alert(user_id: str, node_name: str, node_address: str):
    """Send alert when node comes back online"""
    telegram_user = await db.telegram_users.find_one({"user_id": user_id})
    
    if not telegram_user:
        return
    
    chat_id = telegram_user['chat_id']
    
    message = f"""
✅ **NODE BACK ONLINE**

Node: **{node_name}**
Address: `{node_address[:8]}...{node_address[-8:]}`

🎉 Your node is back online and ready!
"""
    
    await send_telegram_notification(chat_id, message)


def main():
    """Start the bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("nodes", nodes))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("help", help_command))
    
    # Start the bot
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
