import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    API_ID = int(os.getenv("API_ID", 123456))
    API_HASH = os.getenv("API_HASH", "your_api_hash")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
    
    # Database
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "FileFetchBot")
    
    # Channels
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", -1003286415377))
    FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "serenaunzipbot")
    
    # Owner IDs
    OWNER_IDS = list(map(int, os.getenv("OWNER_IDS", "1598576202,6518065496").split(",")))
    
    # Bot Settings
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 2097152000))  # 2GB
    DELETE_AFTER_SEND = True
    AUTO_DELETE_SECONDS = 60  # Delete files after 60 seconds
    
    # Branding
    BRAND_NAME = "TECHNICAL_SERENA"
    OWNER_USERNAME = "technicalserena"
    
    # Thumbnail
    THUMBNAIL_URL = os.getenv("THUMBNAIL_URL", "")
    
    # Premium Plans (in days)
    PREMIUM_PLANS = {
        "basic": 7,
        "standard": 30,
        "premium": 365
    }
