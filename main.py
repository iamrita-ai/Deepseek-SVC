from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, FloodWait
import asyncio
import os
import sys
from datetime import datetime
from flask import Flask

from config import Config
from utils.db import Database
from utils.progress import Progress
from utils.link import LinkParser

# Initialize Flask app for Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return f"{Config.BRAND_NAME} Bot is running!"

# Initialize database
db = Database(Config.MONGO_URL, Config.DATABASE_NAME)

# Initialize bot
app = Client(
    "FileFetchBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Store user sessions
user_sessions = {}

# Start command
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check force subscription
    try:
        user = await client.get_chat_member(Config.FORCE_SUB_CHANNEL, user_id)
        if user.status in ["left", "kicked"]:
            await message.reply_text(
                f"⚠️ **Please join our channel first!**\n\n"
                f"Join: @{Config.FORCE_SUB_CHANNEL}\n"
                f"Then try /start again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{Config.FORCE_SUB_CHANNEL}")]
                ])
            )
            return
    except Exception:
        pass
    
    # Check if user exists in database
    user_data = await db.get_user(user_id)
    if not user_data:
        await db.add_user(user_id, message.from_user.first_name)
    
    welcome_text = f"""
👋 **Welcome to {Config.BRAND_NAME}**

I can fetch files from any Telegram channel/group using your session.

**Available Commands:**
• /login - Login with phone number/OTP
• /batch - Bulk extract messages
• /settings - Configure bot settings
• /myplan - Check your premium plan
• /logout - Logout from session
• /terms - Terms and conditions

**Owner:** @{Config.OWNER_USERNAME}
    """
    
    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔐 Login", callback_data="login"),
             InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("📦 Batch Extract", callback_data="batch"),
             InlineKeyboardButton("👤 My Plan", callback_data="myplan")],
            [InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{Config.OWNER_USERNAME}"),
             InlineKeyboardButton("📢 Channel", url=f"https://t.me/{Config.FORCE_SUB_CHANNEL}")]
        ])
    )

# Login command
@app.on_message(filters.command("login"))
async def login_command(client: Client, message: Message):
    await message.reply_text(
        "🔐 **Login Method**\n\n"
        "Choose how you want to login:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Phone + OTP", callback_data="login_phone")],
            [InlineKeyboardButton("🔑 Session String", callback_data="login_session")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])
    )

# Batch command
@app.on_message(filters.command("batch"))
async def batch_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data or 'session_string' not in user_data:
        await message.reply_text(
            "⚠️ You need to login first!\n"
            "Use /login to login with your account."
        )
        return
    
    await message.reply_text(
        "📦 **Batch Extraction**\n\n"
        "Send me the channel/group link:\n"
        "Format: `https://t.me/c/channel_id/post_id`\n"
        "or just the post link.\n\n"
        "Type /cancel to cancel."
    )
    
    # Store state
    await db.update_user(user_id, {"state": "awaiting_batch_link"})

# Settings command
@app.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        return
    
    settings_text = f"""
⚙️ **Settings - {Config.BRAND_NAME}**

**Current Settings:**
• Chat ID: `{user_data.get('chat_id', 'Not set')}`
• Rename: `{user_data.get('rename', 'Original name')}`
• Caption: `{user_data.get('caption', 'Not set')}`
• Replace Words: `{user_data.get('replace_words', 'None')}`

**Options:**
1. SETCHATID: Set destination chat
2. SETRENAME: Set custom rename pattern
3. CAPTION: Set custom caption
4. REPLACEWORDS: Set words to replace
5. RESET: Reset to defaults
"""
    
    await message.reply_text(
        settings_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 SETCHATID", callback_data="set_chatid"),
             InlineKeyboardButton("📝 SETRENAME", callback_data="set_rename")],
            [InlineKeyboardButton("📄 CAPTION", callback_data="set_caption"),
             InlineKeyboardButton("🔄 REPLACEWORDS", callback_data="set_replacewords")],
            [InlineKeyboardButton("🔄 RESET", callback_data="reset_settings"),
             InlineKeyboardButton("🗑️ CLEAR FILES", callback_data="clear_files")],
            [InlineKeyboardButton("📸 CUSTOM THUMB", callback_data="custom_thumb"),
             InlineKeyboardButton("📄 PDF WATERMARK", callback_data="pdf_watermark")],
            [InlineKeyboardButton("🎥 VIDEO WATERMARK", callback_data="video_watermark")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ])
    )

# Admin commands
@app.on_message(filters.command("add") & filters.user(Config.OWNER_IDS))
async def add_premium(client: Client, message: Message):
    try:
        user_id = int(message.command[1])
        await db.add_premium(user_id, 30)  # 30 days premium
        await message.reply_text(f"✅ User {user_id} added to premium for 30 days")
    except:
        await message.reply_text("Usage: /add user_id")

@app.on_message(filters.command("rem") & filters.user(Config.OWNER_IDS))
async def remove_premium(client: Client, message: Message):
    try:
        user_id = int(message.command[1])
        await db.remove_premium(user_id)
        await message.reply_text(f"✅ User {user_id} removed from premium")
    except:
        await message.reply_text("Usage: /rem user_id")

@app.on_message(filters.command("get") & filters.user(Config.OWNER_IDS))
async def get_users(client: Client, message: Message):
    users = await db.get_all_users()
    text = "👥 **All Users:**\n\n"
    for user in users:
        text += f"ID: {user['user_id']} | Premium: {user.get('premium', False)}\n"
    await message.reply_text(text)

@app.on_message(filters.command("lock") & filters.user(Config.OWNER_IDS))
async def lock_channel(client: Client, message: Message):
    try:
        channel_id = int(message.command[1])
        await db.lock_channel(channel_id)
        await message.reply_text(f"✅ Channel {channel_id} locked")
    except:
        await message.reply_text("Usage: /lock channel_id")

# Message handler for batch processing - FIXED FILTER
@app.on_message(filters.text & ~filters.command)
async def handle_messages(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        return
    
    state = user_data.get('state')
    
    if state == "awaiting_batch_link":
        # Parse the link
        parser = LinkParser(message.text)
        if parser.is_valid():
            await message.reply_text(
                f"✅ Link parsed!\n"
                f"Channel ID: {parser.channel_id}\n"
                f"Post ID: {parser.post_id}\n\n"
                "Now send the number of messages to fetch (1-100):"
            )
            await db.update_user(user_id, {
                "state": "awaiting_batch_count",
                "batch_channel": parser.channel_id,
                "batch_start": parser.post_id
            })
        else:
            await message.reply_text("❌ Invalid link! Please send a valid Telegram link.")
    
    elif state == "awaiting_batch_count":
        try:
            count = int(message.text)
            if 1 <= count <= 100:
                await message.reply_text(
                    f"✅ Will fetch {count} messages.\n\n"
                    "Starting batch extraction... This may take a while."
                )
                
                # Start batch extraction
                await batch_extract(client, message, user_data, count)
                
                await db.update_user(user_id, {"state": None})
            else:
                await message.reply_text("Please send a number between 1-100")
        except:
            await message.reply_text("Please send a valid number")
    
    elif state == "awaiting_phone":
        # Handle phone number input
        from plugins.login import handle_phone_login
        await handle_phone_login(client, message, message.text)
    
    elif state == "awaiting_otp":
        # Handle OTP input
        from plugins.login import handle_otp
        await handle_otp(client, message, message.text)
    
    elif state == "awaiting_password":
        # Handle 2FA password
        from plugins.login import handle_password
        await handle_password(client, message, message.text)
    
    elif state == "awaiting_session":
        # Handle session string
        from plugins.login import handle_session_string
        await handle_session_string(client, message, message.text)

# Callback query handler
@app.on_callback_query()
async def callback_handler(client: Client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "login_phone":
        await callback_query.message.edit_text(
            "📱 **Phone Login**\n\n"
            "Please send your phone number in international format:\n"
            "Example: `+919876543210`\n\n"
            "Type /cancel to cancel."
        )
        await db.update_user(user_id, {"state": "awaiting_phone"})
    
    elif data == "login_session":
        await callback_query.message.edit_text(
            "🔑 **Session Login**\n\n"
            "Please send your Pyrogram session string.\n"
            "Get it from @StringSessionBot\n\n"
            "Type /cancel to cancel."
        )
        await db.update_user(user_id, {"state": "awaiting_session"})
    
    elif data.startswith("set_"):
        setting_type = data[4:]
        await handle_settings(callback_query, setting_type)
    
    elif data == "back_to_main":
        await start_command(client, callback_query.message)
    
    await callback_query.answer()

async def handle_settings(callback_query, setting_type):
    user_id = callback_query.from_user.id
    
    if setting_type == "chatid":
        await callback_query.message.edit_text(
            "💬 **Set Chat ID**\n\n"
            "Send the chat ID where you want files to be sent.\n"
            "Format: `-1001234567890` for channels\n"
            "Just the user ID for DMs."
        )
        await db.update_user(user_id, {"state": "awaiting_chatid"})
    
    elif setting_type == "rename":
        await callback_query.message.edit_text(
            "📝 **Set Rename Pattern**\n\n"
            "Send the rename pattern.\n"
            "Use variables:\n"
            "• {filename} - Original filename\n"
            "• {episode} - Episode number\n"
            "• {quality} - Video quality\n"
            "• {date} - Current date\n\n"
            "Example: `{filename}_[SERENA]`"
        )
        await db.update_user(user_id, {"state": "awaiting_rename"})
    
    elif setting_type == "caption":
        await callback_query.message.edit_text(
            "📄 **Set Custom Caption**\n\n"
            "Send the caption template.\n"
            "Use variables:\n"
            "• {filename} - Filename\n"
            "• {size} - File size\n"
            "• {duration} - Video duration\n\n"
            "Example: `📁 {filename}\\n📦 Size: {size}`"
        )
        await db.update_user(user_id, {"state": "awaiting_caption"})
    
    elif setting_type == "replacewords":
        await callback_query.message.edit_text(
            "🔄 **Set Replace Words**\n\n"
            "Send words to replace (comma separated):\n"
            "Format: `old1:new1, old2:new2`\n\n"
            "Example: `Vegamovies:SERENA, 480p:HD`"
        )
        await db.update_user(user_id, {"state": "awaiting_replacewords"})

# Batch extraction function
async def batch_extract(client: Client, message: Message, user_data: dict, count: int):
    user_id = message.from_user.id
    session_string = user_data.get('session_string')
    channel_id = user_data.get('batch_channel')
    start_id = user_data.get('batch_start')
    
    try:
        # Create user client from session
        user_client = Client(
            f"user_{user_id}",
            session_string=session_string,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH
        )
        
        await user_client.start()
        
        # Fetch messages
        messages = []
        async for msg in user_client.get_chat_history(
            chat_id=channel_id,
            limit=count,
            offset_id=start_id
        ):
            messages.append(msg)
        
        # Forward messages
        dest_chat = user_data.get('chat_id', user_id)
        progress_msg = await message.reply_text("📤 Starting upload...")
        
        for i, msg in enumerate(messages):
            try:
                # Create progress callback
                progress = Progress(
                    client=client,
                    chat_id=message.chat.id,
                    message_id=progress_msg.id,
                    index=i,
                    total=len(messages)
                )
                
                # Forward message
                if msg.document or msg.video or msg.audio:
                    # Download file
                    file_path = await msg.download(
                        progress=progress.progress_callback
                    )
                    
                    # Send to user
                    await client.send_document(
                        chat_id=dest_chat,
                        document=file_path,
                        caption=user_data.get('caption', ''),
                        progress=progress.progress_callback
                    )
                    
                    # Delete file from server
                    if Config.DELETE_AFTER_SEND:
                        await asyncio.sleep(Config.AUTO_DELETE_SECONDS)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                
                elif msg.text:
                    await client.send_message(dest_chat, msg.text)
                
                # Log to channel
                await log_to_channel(client, user_id, msg)
                
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)}")
        
        await progress_msg.edit_text(f"✅ Batch extraction complete!\nSent {len(messages)} messages.")
        
        await user_client.stop()
        
    except Exception as e:
        await message.reply_text(f"❌ Extraction failed: {str(e)}")

# Log function
async def log_to_channel(client: Client, user_id: int, message):
    try:
        log_text = f"""
📥 **New Extraction - {Config.BRAND_NAME}**

**User:** `{user_id}`
**Chat:** `{message.chat.id}`
**Message ID:** `{message.id}`
**Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

"""
        if message.caption:
            log_text += f"**Caption:** {message.caption[:100]}...\n"
        
        await client.send_message(
            Config.LOG_CHANNEL,
            log_text
        )
        
        if message.document or message.video:
            await client.send_document(
                Config.LOG_CHANNEL,
                message.document.file_id if message.document else message.video.file_id
            )
    except:
        pass

# Cancel command
@app.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    user_id = message.from_user.id
    await db.update_user(user_id, {"state": None})
    await message.reply_text("✅ Operation cancelled.")

# Logout command
@app.on_message(filters.command("logout"))
async def logout_command(client: Client, message: Message):
    user_id = message.from_user.id
    await db.delete_session(user_id)
    await message.reply_text("✅ Logged out successfully.")

# My Plan command
@app.on_message(filters.command("myplan"))
async def myplan_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        return
    
    plan_text = f"""
👤 **Your Plan - {Config.BRAND_NAME}**

**Status:** {'✅ PREMIUM' if user_data.get('premium') else '🆓 FREE'}
"""
    
    if user_data.get('premium_expiry'):
        expiry = user_data['premium_expiry'].strftime('%Y-%m-%d %H:%M:%S')
        plan_text += f"**Expiry:** {expiry}\n"
    
    plan_text += f"""
**Features:**
• Batch extraction: {('✅' if user_data.get('premium') else '❌')} 100 messages
• Max file size: {('✅' if user_data.get('premium') else '❌')} 2GB
• Priority support: {('✅' if user_data.get('premium') else '❌')}

**Upgrade:** Contact @{Config.OWNER_USERNAME}
"""
    
    await message.reply_text(plan_text)

# Terms command
@app.on_message(filters.command("terms"))
async def terms_command(client: Client, message: Message):
    terms_text = f"""
📜 **Terms & Conditions - {Config.BRAND_NAME}**

1. This bot is for personal use only.
2. Do not use for copyright infringement.
3. We are not responsible for misuse.
4. Premium plans are non-refundable.
5. Follow Telegram Terms of Service.

**Contact:** @{Config.OWNER_USERNAME}
"""
    await message.reply_text(terms_text)

# Start the bot with Flask
def run():
    import threading
    import time
    
    # Start Flask in a separate thread
    def run_flask():
        web_app.run(host='0.0.0.0', port=10000, debug=False)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Pyrogram bot
    print(f"🤖 {Config.BRAND_NAME} Bot Starting...")
    app.run()

if __name__ == "__main__":
    run()
