from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

def register_start_handlers(app, db):
    @app.on_message(filters.command("start"))
    async def start_command(client, message: Message):
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
    
    @app.on_message(filters.command("myplan"))
    async def myplan_command(client, message: Message):
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
    
    @app.on_message(filters.command("terms"))
    async def terms_command(client, message: Message):
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
    
    @app.on_message(filters.command("logout"))
    async def logout_command(client, message: Message):
        user_id = message.from_user.id
        await db.delete_session(user_id)
        await message.reply_text("✅ Logged out successfully.")
    
    @app.on_message(filters.command("cancel"))
    async def cancel_command(client, message: Message):
        user_id = message.from_user.id
        await db.update_user(user_id, {"state": None})
        await message.reply_text("✅ Operation cancelled.")
