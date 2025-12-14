from pyrogram import Client, filters, idle
from pyrogram.types import Message
import threading
from flask import Flask
import os

from config import Config
from utils.db import Database

# Initialize Flask app for Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return f"{Config.BRAND_NAME} Bot is running!"

@web_app.route('/health')
def health():
    return "OK", 200

# Initialize database
db = Database(Config.MONGO_URL, Config.DATABASE_NAME)

# Initialize bot
app = Client(
    "FileFetchBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Import plugins
from plugins.start import register_start_handlers
from plugins.login import register_login_handlers
from plugins.batch import register_batch_handlers
from plugins.settings import register_settings_handlers
from plugins.admin import register_admin_handlers
from plugins.callback import register_callback_handlers

# Register all handlers
register_start_handlers(app, db)
register_login_handlers(app, db)
register_batch_handlers(app, db)
register_settings_handlers(app, db)
register_admin_handlers(app, db)
register_callback_handlers(app, db)

# Message handler for text messages (not commands)
@app.on_message(filters.text & ~filters.command)
async def handle_text_messages(client, message):
    from plugins.batch import handle_user_states
    await handle_user_states(client, message, db)

# Run Flask server in a thread
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Main function
def main():
    # Start Flask in a separate thread for Render
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print(f"🤖 {Config.BRAND_NAME} Bot Starting...")
    print(f"🔗 Web server running on port {os.environ.get('PORT', 10000)}")
    print(f"👑 Owner IDs: {Config.OWNER_IDS}")
    
    # Start Pyrogram bot
    app.run()

if __name__ == "__main__":
    main()
