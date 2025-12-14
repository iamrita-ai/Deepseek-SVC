from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime

from config import Config
from utils.db import Database

db = Database(Config.MONGO_URL, Config.DATABASE_NAME)

@app.on_message(filters.command("stats") & filters.user(Config.OWNER_IDS))
async def stats_command(client: Client, message: Message):
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

@app.on_message(filters.command("broadcast") & filters.user(Config.OWNER_IDS))
async def broadcast_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast your_message")
        return
    
    broadcast_text = " ".join(message.command[1:])
    users = await db.get_all_users()
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await client.send_message(user['user_id'], broadcast_text)
            sent += 1
        except:
            failed += 1
        await asyncio.sleep(0.1)  # Prevent flooding
    
    await message.reply_text(
        f"📢 Broadcast Complete!\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}"
  )
