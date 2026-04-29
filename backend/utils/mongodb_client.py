"""
MongoDB Client for SwarmBharat AI
Production-ready MongoDB Atlas integration with free tier support
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import motor.motor_asyncio
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class MongoDBClient:
    """Async MongoDB client with connection management"""
    
    def __init__(self):
        # Try production MongoDB first, fallback to local
        self.connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/swarmbharat')
        self.db_name = os.getenv('MONGODB_DB_NAME', 'swarmbharat')
        self.client = None
        self.db = None
        self.connected = False
        self.using_local = "localhost" in self.connection_string
        
    async def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            if not self.connection_string:
                logger.warning("MongoDB URI not provided, using fallback storage")
                return False
                
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)
            # Test connection
            await self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            
            # Create indexes for better performance
            await self._create_indexes()
            
            logger.info("✅ Connected to MongoDB Atlas")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            return False
    
    async def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Users collection indexes
            await self.db.users.create_index("user_id", unique=True)
            await self.db.users.create_index("created_at")
            
            # Conversations collection indexes
            await self.db.conversations.create_index([("user_id", 1), ("timestamp", -1)])
            await self.db.conversations.create_index("timestamp")
            
            # Documents collection indexes
            await self.db.documents.create_index("user_id")
            await self.db.documents.create_index("uploaded_at")
            
            # User memory collection indexes
            await self.db.user_memory.create_index("user_id", unique=True)
            
            logger.info("✅ MongoDB indexes created")
            
        except Exception as e:
            logger.error(f"Index creation failed: {str(e)}")
    
    async def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Save or update user profile"""
        try:
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        **profile_data,
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "user_id": user_id,
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save user profile: {str(e)}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            profile = await self.db.users.find_one({"user_id": user_id})
            if profile:
                # Convert ObjectId to string
                profile["_id"] = str(profile["_id"])
                return profile
            return None
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            return None
    
    async def save_conversation(self, user_id: str, conversation_data: Dict[str, Any]):
        """Save conversation message"""
        try:
            await self.db.conversations.insert_one({
                "user_id": user_id,
                "timestamp": datetime.now(),
                **conversation_data
            })
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {str(e)}")
            return False
    
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        try:
            conversations = await self.db.conversations.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)
            
            # Convert ObjectId to string
            for conv in conversations:
                conv["_id"] = str(conv["_id"])
                
            return conversations
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []
    
    async def save_document(self, user_id: str, document_data: Dict[str, Any]):
        """Save document metadata"""
        try:
            await self.db.documents.insert_one({
                "user_id": user_id,
                "uploaded_at": datetime.now(),
                **document_data
            })
            return True
        except Exception as e:
            logger.error(f"Failed to save document: {str(e)}")
            return False
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's uploaded documents"""
        try:
            documents = await self.db.documents.find(
                {"user_id": user_id}
            ).sort("uploaded_at", -1).to_list(length=None)
            
            # Convert ObjectId to string
            for doc in documents:
                doc["_id"] = str(doc["_id"])
                
            return documents
        except Exception as e:
            logger.error(f"Failed to get user documents: {str(e)}")
            return []
    
    async def save_user_memory(self, user_id: str, memory_data: Dict[str, Any]):
        """Save user memory and preferences"""
        try:
            await self.db.user_memory.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        **memory_data,
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "user_id": user_id,
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save user memory: {str(e)}")
            return False
    
    async def get_user_memory(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user memory and preferences"""
        try:
            memory = await self.db.user_memory.find_one({"user_id": user_id})
            if memory:
                memory["_id"] = str(memory["_id"])
                return memory
            return None
        except Exception as e:
            logger.error(f"Failed to get user memory: {str(e)}")
            return None
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get database usage statistics"""
        try:
            stats = {
                "users_count": await self.db.users.count_documents({}),
                "conversations_count": await self.db.conversations.count_documents({}),
                "documents_count": await self.db.documents.count_documents({}),
                "memory_count": await self.db.user_memory.count_documents({})
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            return {}
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global MongoDB instance
mongodb_client = MongoDBClient()
