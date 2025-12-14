from pyrogram import filters
from pyrogram.types import Message
import asyncio
import os
from datetime import datetime

from config import Config
from utils.link import LinkParser
from utils.progress import Progress

async def handle_user_states(client, message, db):
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
                await batch_extract(client, message, user_data, count, db)
                
                await db.update_user(user_id, {"state": None})
            else:
                await message.reply_text("Please send a number between 1-100")
        except:
            await message.reply_text("Please send a valid number")
    
    elif state == "awaiting_phone":
        from plugins.login import handle_phone_login
        await handle_phone_login(client, message, message.text)
    
    elif state == "awaiting_otp":
        from plugins.login import handle_otp
        await handle_otp(client, message, message.text)
    
    elif state == "awaiting_password":
        from plugins.login import handle_password
        await handle_password(client, message, message.text)
    
    elif state == "awaiting_session":
        from plugins.login import handle_session_string
        await handle_session_string(client, message, message.text)

async def batch_extract(client, message, user_data, count, db):
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

async def log_to_channel(client, user_id, message):
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
    except Exception as e:
        print(f"Log error: {e}")

def register_batch_handlers(app, db):
    @app.on_message(filters.command("batch"))
    async def batch_command(client, message: Message):
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
