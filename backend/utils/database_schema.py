"""
MongoDB Atlas Database Schema for SwarmBharat AI
Defines collections and indexes for production database
"""

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseSchema:
    """MongoDB Atlas database schema manager"""
    
    def __init__(self, client: MongoClient, db_name: str = "swarmbharat"):
        self.client = client
        self.db = client[db_name]
        self.collections = self._define_collections()
    
    def _define_collections(self) -> dict:
        """Define all collections and their schemas"""
        return {
            "users": {
                "schema": {
                    "_id": "string (user_id)",
                    "email": "string",
                    "mobile": "string",
                    "profile": {
                        "basic_info": {
                            "age": "number",
                            "gender": "string",
                            "state": "string",
                            "city": "string",
                            "education": "string"
                        },
                        "career_profile": {
                            "employment_status": "string",
                            "industry": "string",
                            "current_role": "string",
                            "years_experience": "number",
                            "monthly_income": "number",
                            "company_name": "string"
                        },
                        "financial_profile": {
                            "risk_tolerance": "string",
                            "investment_experience": "string",
                            "financial_goals": ["string"]
                        },
                        "preferences": {
                            "language": "string",
                            "preferred_tone": "string",
                            "domain_interests": ["string"]
                        }
                    },
                    "verification": {
                        "email_verified": "boolean",
                        "mobile_verified": "boolean",
                        "aadhaar_verified": "boolean",
                        "pan_verified": "boolean"
                    },
                    "subscription": {
                        "tier": "string (free/premium)",
                        "expires_at": "datetime",
                        "features": ["string"]
                    },
                    "created_at": "datetime",
                    "updated_at": "datetime",
                    "last_login": "datetime"
                },
                "indexes": [
                    {"keys": {"email": 1}, "unique": True},
                    {"keys": {"mobile": 1}, "unique": True},
                    {"keys": {"profile.basic_info.state": 1}},
                    {"keys": {"profile.career_profile.employment_status": 1}},
                    {"keys": {"subscription.tier": 1}},
                    {"keys": {"created_at": 1}}
                ]
            },
            
            "conversations": {
                "schema": {
                    "_id": "string (conversation_id)",
                    "user_id": "string",
                    "domain": "string",
                    "messages": [
                        {
                            "id": "string",
                            "role": "string (user/bot)",
                            "content": "string",
                            "timestamp": "datetime",
                            "metadata": {
                                "agent": "string (if debate)",
                                "confidence": "number",
                                "sources": ["string"],
                                "processing_time": "number"
                            }
                        }
                    ],
                    "context": {
                        "query_type": "string",
                        "personalization_applied": "boolean",
                        "agents_used": ["string"]
                    },
                    "feedback": {
                        "rating": "number (1-5)",
                        "comment": "string",
                        "helpful": "boolean"
                    },
                    "created_at": "datetime",
                    "updated_at": "datetime"
                },
                "indexes": [
                    {"keys": {"user_id": 1, "created_at": -1}},
                    {"keys": {"domain": 1}},
                    {"keys": {"messages.timestamp": -1}},
                    {"keys": {"created_at": -1}},
                    {"keys": {"feedback.rating": 1}}
                ]
            },
            
            "documents": {
                "schema": {
                    "_id": "string (document_id)",
                    "user_id": "string",
                    "filename": "string",
                    "file_type": "string",
                    "file_size": "number",
                    "file_path": "string",
                    "content": "string (extracted text)",
                    "metadata": {
                        "upload_date": "datetime",
                        "processed": "boolean",
                        "pages": "number",
                        "language": "string"
                    },
                    "embeddings": ["number"],
                    "created_at": "datetime"
                },
                "indexes": [
                    {"keys": {"user_id": 1, "created_at": -1}},
                    {"keys": {"filename": 1}},
                    {"keys": {"file_type": 1}},
                    {"keys": {"created_at": -1}}
                ]
            },
            
            "government_services": {
                "schema": {
                    "_id": "string (service_id)",
                    "user_id": "string",
                    "service_type": "string (pm_kisan, epfo, scholarship, etc.)",
                    "service_data": {
                        "application_id": "string",
                        "status": "string (pending/approved/rejected)",
                        "amount": "number",
                        "benefit_type": "string"
                    },
                    "api_responses": {
                        "verification": "object",
                        "status_check": "object",
                        "last_updated": "datetime"
                    },
                    "created_at": "datetime",
                    "updated_at": "datetime"
                },
                "indexes": [
                    {"keys": {"user_id": 1, "service_type": 1}},
                    {"keys": {"service_type": 1}},
                    {"keys": {"service_data.status": 1}},
                    {"keys": {"updated_at": -1}}
                ]
            },
            
            "analytics": {
                "schema": {
                    "_id": "string (analytics_id)",
                    "user_id": "string",
                    "event_type": "string (query, login, signup, etc.)",
                    "event_data": {
                        "domain": "string",
                        "query_length": "number",
                        "response_time": "number",
                        "agent_used": "string",
                        "features_used": ["string"]
                    },
                    "session_id": "string",
                    "ip_address": "string",
                    "user_agent": "string",
                    "created_at": "datetime"
                },
                "indexes": [
                    {"keys": {"user_id": 1, "created_at": -1}},
                    {"keys": {"event_type": 1}},
                    {"keys": {"session_id": 1}},
                    {"keys": {"created_at": -1}},
                    {"keys": {"event_data.domain": 1}}
                ]
            },
            
            "debates": {
                "schema": {
                    "_id": "string (debate_id)",
                    "user_id": "string",
                    "query": "string",
                    "domain": "string",
                    "agents": [
                        {
                            "name": "string",
                            "response": "string",
                            "confidence": "number",
                            "reasoning": "string",
                            "sources": ["string"],
                            "processing_time": "number"
                        }
                    ],
                    "synthesis": {
                        "final_answer": "string",
                        "overall_confidence": "number",
                        "agent_agreements": "object",
                        "key_insights": ["string"]
                    },
                    "user_feedback": {
                        "helpful": "boolean",
                        "accuracy": "number (1-5)",
                        "comment": "string"
                    },
                    "created_at": "datetime"
                },
                "indexes": [
                    {"keys": {"user_id": 1, "created_at": -1}},
                    {"keys": {"domain": 1}},
                    {"keys": {"created_at": -1}},
                    {"keys": {"synthesis.overall_confidence": 1}}
                ]
            },
            
            "user_sessions": {
                "schema": {
                    "_id": "string (session_id)",
                    "user_id": "string",
                    "session_data": {
                        "ip_address": "string",
                        "user_agent": "string",
                        "location": "string",
                        "device_type": "string"
                    },
                    "activity": [
                        {
                            "timestamp": "datetime",
                            "action": "string",
                            "details": "object"
                        }
                    ],
                    "created_at": "datetime",
                    "expires_at": "datetime",
                    "last_activity": "datetime"
                },
                "indexes": [
                    {"keys": {"user_id": 1, "last_activity": -1}},
                    {"keys": {"session_id": 1},
                    {"keys": {"expires_at": 1}},
                    {"keys": {"created_at": -1}}
                ]
            }
        }
    
    async def create_collections(self):
        """Create all collections with schemas and indexes"""
        for collection_name, config in self.collections.items():
            try:
                # Create collection
                collection = self.db[collection_name]
                
                # Create indexes
                for index_config in config.get("indexes", []):
                    try:
                        await collection.create_index(
                            index_config["keys"],
                            unique=index_config.get("unique", False)
                        )
                        logger.info(f"Created index for {collection_name}: {index_config['keys']}")
                    except Exception as e:
                        logger.warning(f"Index creation failed for {collection_name}: {str(e)}")
                
                logger.info(f"✅ Collection '{collection_name}' ready")
                
            except CollectionInvalid as e:
                logger.warning(f"Collection '{collection_name}' already exists: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to create collection '{collection_name}': {str(e)}")
    
    async def get_collection_stats(self) -> dict:
        """Get statistics for all collections"""
        stats = {}
        for collection_name in self.collections.keys():
            try:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = {
                    "document_count": count,
                    "size_bytes": await self._get_collection_size(collection),
                    "indexes": await self._get_collection_indexes(collection)
                }
            except Exception as e:
                stats[collection_name] = {"error": str(e)}
        
        return stats
    
    async def _get_collection_size(self, collection) -> int:
        """Get collection size in bytes"""
        try:
            stats = await collection.estimated_document_count()
            return stats * 1024  # Rough estimate
        except:
            return 0
    
    async def _get_collection_indexes(self, collection) -> list:
        """Get collection indexes"""
        try:
            indexes = await collection.list_indexes()
            return [idx["name"] for idx in indexes]
        except:
            return []
    
    async def seed_initial_data(self):
        """Seed initial data for production"""
        try:
            # Create admin user
            admin_user = {
                "_id": "admin",
                "email": "admin@swarmbharat.ai",
                "profile": {
                    "basic_info": {
                        "age": 30,
                        "gender": "Other",
                        "state": "Maharashtra",
                        "city": "Mumbai",
                        "education": "Post Graduate"
                    },
                    "career_profile": {
                        "employment_status": "Employed",
                        "industry": "Technology",
                        "current_role": "System Administrator",
                        "years_experience": 5,
                        "monthly_income": 150000
                    },
                    "preferences": {
                        "language": "English",
                        "preferred_tone": "Professional"
                    }
                },
                "verification": {
                    "email_verified": True,
                    "mobile_verified": False,
                    "aadhaar_verified": False,
                    "pan_verified": False
                },
                "subscription": {
                    "tier": "premium",
                    "features": ["all"]
                },
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "last_login": datetime.now()
            }
            
            users_collection = self.db["users"]
            await users_collection.update_one(
                {"_id": "admin"},
                {"$setOnInsert": admin_user},
                upsert=True
            )
            
            logger.info("✅ Initial data seeded successfully")
            
        except Exception as e:
            logger.error(f"Failed to seed initial data: {str(e)}")

# Database setup function
async def setup_database(client: MongoClient, db_name: str = "swarmbharat"):
    """Setup complete database with schema and initial data"""
    schema = DatabaseSchema(client, db_name)
    await schema.create_collections()
    await schema.seed_initial_data()
    return schema
