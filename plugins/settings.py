from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

def register_settings_handlers(app, db):
    @app.on_message(filters.command("settings"))
    async def settings_command(client, message: Message):
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
