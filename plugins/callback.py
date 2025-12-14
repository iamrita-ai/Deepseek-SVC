from pyrogram.types import CallbackQuery
from config import Config

def register_callback_handlers(app, db):
    @app.on_callback_query()
    async def callback_handler(client, callback_query: CallbackQuery):
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
            await handle_settings(callback_query, setting_type, db)
        
        elif data == "back_to_main":
            from plugins.start import start_command
            await start_command(client, callback_query.message)
        
        elif data == "cancel":
            await db.update_user(user_id, {"state": None})
            await callback_query.message.edit_text("✅ Operation cancelled.")
        
        elif data == "reset_settings":
            await db.update_user(user_id, {
                "chat_id": None,
                "rename": None,
                "caption": None,
                "replace_words": None
            })
            await callback_query.message.edit_text("✅ All settings reset to default.")
        
        elif data == "batch":
            from plugins.batch import batch_command
            await batch_command(client, callback_query.message)
        
        elif data == "myplan":
            from plugins.start import myplan_command
            await myplan_command(client, callback_query.message)
        
        elif data == "settings":
            from plugins.settings import settings_command
            await settings_command(client, callback_query.message)
        
        await callback_query.answer()

async def handle_settings(callback_query, setting_type, db):
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
