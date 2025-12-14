from pyrogram import filters
from pyrogram.types import Message
from datetime import datetime
from config import Config

def register_admin_handlers(app, db):
    @app.on_message(filters.command("add") & filters.user(Config.OWNER_IDS))
    async def add_premium(client, message: Message):
        try:
            user_id = int(message.command[1])
            await db.add_premium(user_id, 30)  # 30 days premium
            await message.reply_text(f"✅ User {user_id} added to premium for 30 days")
        except:
            await message.reply_text("Usage: /add user_id")
    
    @app.on_message(filters.command("rem") & filters.user(Config.OWNER_IDS))
    async def remove_premium(client, message: Message):
        try:
            user_id = int(message.command[1])
            await db.remove_premium(user_id)
            await message.reply_text(f"✅ User {user_id} removed from premium")
        except:
            await message.reply_text("Usage: /rem user_id")
    
    @app.on_message(filters.command("get") & filters.user(Config.OWNER_IDS))
    async def get_users(client, message: Message):
        users = await db.get_all_users()
        text = "👥 **All Users:**\n\n"
        for user in users:
            text += f"ID: {user['user_id']} | Premium: {user.get('premium', False)}\n"
        await message.reply_text(text)
    
    @app.on_message(filters.command("lock") & filters.user(Config.OWNER_IDS))
    async def lock_channel(client, message: Message):
        try:
            channel_id = int(message.command[1])
            await db.lock_channel(channel_id)
            await message.reply_text(f"✅ Channel {channel_id} locked")
        except:
            await message.reply_text("Usage: /lock channel_id")
    
    @app.on_message(filters.command("stats") & filters.user(Config.OWNER_IDS))
    async def stats_command(client, message: Message):
        users = await db.get_all_users()
        total_users = len(users)
        premium_users = len([u for u in users if u.get('premium', False)])
        
        stats_text = f"""
📊 **Bot Statistics - {Config.BRAND_NAME}**

**Users:** {total_users}
**Premium Users:** {premium_users}
**Active Sessions:** {len([u for u in users if u.get('session_string')])}

**Server Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await message.reply_text(stats_text)
