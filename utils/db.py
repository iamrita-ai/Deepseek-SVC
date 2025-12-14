from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self, uri, database_name):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]
        self.users = self.db.users
        self.channels = self.db.channels
        self.settings = self.db.settings
    
    async def add_user(self, user_id, first_name):
        user_data = {
            "user_id": user_id,
            "first_name": first_name,
            "join_date": datetime.now(),
            "premium": False,
            "premium_expiry": None,
            "session_string": None,
            "chat_id": None,
            "rename": None,
            "caption": None,
            "replace_words": [],
            "state": None,
            "banned": False
        }
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": user_data},
            upsert=True
        )
    
    async def get_user(self, user_id):
        return await self.users.find_one({"user_id": user_id})
    
    async def update_user(self, user_id, data):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": data}
        )
    
    async def add_premium(self, user_id, days):
        expiry = datetime.now() + timedelta(days=days)
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "premium": True,
                "premium_expiry": expiry
            }}
        )
    
    async def remove_premium(self, user_id):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "premium": False,
                "premium_expiry": None
            }}
        )
    
    async def get_all_users(self):
        return await self.users.find().to_list(None)
    
    async def lock_channel(self, channel_id):
        await self.channels.update_one(
            {"channel_id": channel_id},
            {"$set": {"locked": True}},
            upsert=True
        )
    
    async def is_channel_locked(self, channel_id):
        channel = await self.channels.find_one({"channel_id": channel_id})
        return channel.get("locked", False) if channel else False
    
    async def save_session(self, user_id, session_string):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"session_string": session_string}}
        )
    
    async def delete_session(self, user_id):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"session_string": None}}
        )
