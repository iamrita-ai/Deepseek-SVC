from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
import asyncio

from config import Config

# Store OTP codes temporarily
otp_storage = {}

def register_login_handlers(app, db):
    @app.on_message(filters.command("login"))
    async def login_command(client, message: Message):
        await message.reply_text(
            "🔐 **Login Method**\n\n"
            "Choose how you want to login:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Phone + OTP", callback_data="login_phone")],
                [InlineKeyboardButton("🔑 Session String", callback_data="login_session")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )
    
    # Functions to handle different login states
    async def handle_phone_login(client: app, message: Message, phone_number: str):
        user_id = message.from_user.id
        
        try:
            # Create a new client for user
            user_client = app(
                f"user_{user_id}",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                device_model="FileFetchBot",
                system_version="1.0",
                app_version="1.0"
            )
            
            await user_client.connect()
            
            # Send code
            sent_code = await user_client.send_code(phone_number)
            
            # Store code info
            otp_storage[user_id] = {
                "client": user_client,
                "phone_number": phone_number,
                "phone_code_hash": sent_code.phone_code_hash
            }
            
            await message.reply_text(
                "✅ Verification code sent!\n\n"
                "Please send the OTP in this format:\n"
                "`6 5 7 8 3 1` (with spaces)\n\n"
                "Or just `657831` without spaces."
            )
            
            await db.update_user(user_id, {"state": "awaiting_otp"})
            
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_otp(client: app, message: Message, otp_code: str):
        user_id = message.from_user.id
        
        if user_id not in otp_storage:
            await message.reply_text("❌ No pending login request. Start with /login")
            return
        
        try:
            user_data = otp_storage[user_id]
            user_client = user_data["client"]
            
            # Clean OTP code (remove spaces)
            otp_clean = otp_code.replace(" ", "")
            
            # Sign in
            try:
                await user_client.sign_in(
                    phone_number=user_data["phone_number"],
                    phone_code_hash=user_data["phone_code_hash"],
                    phone_code=otp_clean
                )
            except SessionPasswordNeeded:
                await message.reply_text(
                    "🔒 Two-step verification enabled.\n"
                    "Please send your password:"
                )
                await db.update_user(user_id, {"state": "awaiting_password"})
                return
            
            # Get session string
            session_string = await user_client.export_session_string()
            
            # Save to database
            await db.save_session(user_id, session_string)
            
            # Stop client
            await user_client.disconnect()
            
            # Clean up
            del otp_storage[user_id]
            
            await message.reply_text(
                "✅ Login successful!\n"
                "Your session has been saved.\n\n"
                "You can now use /batch to extract files."
            )
            
            await db.update_user(user_id, {"state": None})
            
        except PhoneCodeInvalid:
            await message.reply_text("❌ Invalid OTP code. Please try /login again.")
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_password(client: app, message: Message, password: str):
        user_id = message.from_user.id
        
        if user_id not in otp_storage:
            await message.reply_text("❌ No pending login request.")
            return
        
        try:
            user_data = otp_storage[user_id]
            user_client = user_data["client"]
            
            # Sign in with password
            await user_client.check_password(password)
            
            # Get session string
            session_string = await user_client.export_session_string()
            
            # Save to database
            await db.save_session(user_id, session_string)
            
            # Stop client
            await user_client.disconnect()
            
            # Clean up
            del otp_storage[user_id]
            
            await message.reply_text("✅ Login successful! Your session has been saved.")
            await db.update_user(user_id, {"state": None})
            
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_session_string(client: app, message: Message, session_string: str):
        user_id = message.from_user.id
        
        try:
            # Test the session
            test_client = app(
                f"test_{user_id}",
                session_string=session_string,
                api_id=Config.API_ID,
                api_hash=Config.API_HASH
            )
            
            await test_client.connect()
            me = await test_client.get_me()
            await test_client.disconnect()
            
            # Save to database
            await db.save_session(user_id, session_string)
            
            await message.reply_text(
                f"✅ Session saved!\n"
                f"Logged in as: {me.first_name}\n"
                f"Username: @{me.username}"
            )
            
            await db.update_user(user_id, {"state": None})
            
        except Exception as e:
            await message.reply_text(f"❌ Invalid session string: {str(e)}")
    
    # Export functions for use in main.py
    return {
        "handle_phone_login": handle_phone_login,
        "handle_otp": handle_otp,
        "handle_password": handle_password,
        "handle_session_string": handle_session_string
            }
