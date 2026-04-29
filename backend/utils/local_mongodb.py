"""
Local MongoDB Setup for SwarmBharat AI
Fallback option if Atlas setup fails
"""

import motor.motor_asyncio
from pymongo import MongoClient
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class LocalMongoDB:
    """Local MongoDB for development/backup"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/swarmbharat"):
        self.connection_string = connection_string
        self.client = None
        self.db = None
    
    async def connect(self) -> bool:
        """Connect to local MongoDB"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            self.db = self.client.swarmbharat
            await self.client.admin.command('ping')
            logger.info("✅ Connected to local MongoDB")
            return True
        except Exception as e:
            logger.warning(f"Local MongoDB connection failed: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
    
    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create user in local MongoDB"""
        try:
            collection = self.db.users
            await collection.insert_one(user_data)
            return True
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user from local MongoDB"""
        try:
            collection = self.db.users
            user = await collection.find_one({"_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user in local MongoDB"""
        try:
            collection = self.db.users
            await collection.update_one(
                {"_id": user_id},
                {"$set": updates}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            return False
    
    async def save_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        """Save conversation to local MongoDB"""
        try:
            collection = self.db.conversations
            await collection.insert_one(conversation_data)
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {str(e)}")
            return False
    
    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user conversations from local MongoDB"""
        try:
            collection = self.db.conversations
            cursor = collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            conversations = await cursor.to_list(length=limit)
            return conversations
        except Exception as e:
            logger.error(f"Failed to get conversations: {str(e)}")
            return []
    
    async def save_analytics(self, analytics_data: Dict[str, Any]) -> bool:
        """Save analytics to local MongoDB"""
        try:
            collection = self.db.analytics
            await collection.insert_one(analytics_data)
            return True
        except Exception as e:
            logger.error(f"Failed to save analytics: {str(e)}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            collections = ["users", "conversations", "analytics", "debates"]
            
            for collection_name in collections:
                try:
                    collection = self.db[collection_name]
                    count = await collection.count_documents({})
                    stats[collection_name] = count
                except:
                    stats[collection_name] = 0
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}

# Global local MongoDB instance
local_mongodb = LocalMongoDB()

async def init_local_mongodb() -> LocalMongoDB:
    """Initialize local MongoDB"""
    await local_mongodb.connect()
    return local_mongodb
