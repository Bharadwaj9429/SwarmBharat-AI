"""
Firebase Configuration for SwarmBharat AI
Handles authentication, file storage, and Firestore
"""

import firebase_admin
from firebase_admin import credentials, auth, storage, firestore
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Firebase manager for authentication and storage"""
    
    def __init__(self, project_id: str, service_account_path: str = None):
        self.project_id = project_id
        self.service_account_path = service_account_path
        self.app = None
        self.auth_client = None
        self.storage_client = None
        self.firestore_client = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Firebase with service account"""
        try:
            if self.service_account_path and os.path.exists(self.service_account_path):
                # Use service account file
                cred = credentials.Certificate(self.service_account_path)
            else:
                # Use environment variables
                service_account_info = {
                    "type": os.getenv("FIREBASE_TYPE", "service_account"),
                    "project_id": self.project_id,
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
                cred = credentials.Certificate(service_account_info)
            
            # Initialize Firebase app
            self.app = firebase_admin.initialize_app(cred, {
                'projectId': self.project_id,
                'storageBucket': f'{self.project_id}.appspot.com'
            }, name='swarmbharat')
            
            # Initialize services
            self.auth_client = auth.Client(self.app)
            self.storage_client = storage.Client(self.app)
            self.firestore_client = firestore.Client(self.app)
            
            self.initialized = True
            logger.info("✅ Firebase initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            return False
    
    # Authentication Methods
    async def create_user(self, email: str, password: str, display_name: str = None) -> Optional[Dict[str, Any]]:
        """Create Firebase user"""
        try:
            user_record = self.auth_client.create_user(
                email=email,
                password=password,
                display_name=display_name or email.split('@')[0]
            )
            
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "created_at": user_record.user_metadata.creation_timestamp
            }
        except Exception as e:
            logger.error(f"Failed to create Firebase user: {str(e)}")
            return None
    
    async def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token"""
        try:
            decoded_token = self.auth_client.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Failed to verify ID token: {str(e)}")
            return None
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get Firebase user by UID"""
        try:
            user_record = self.auth_client.get_user(uid)
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "display_name": user_record.display_name,
                "email_verified": user_record.email_verified,
                "disabled": user_record.disabled
            }
        except Exception as e:
            logger.error(f"Failed to get Firebase user: {str(e)}")
            return None
    
    async def update_user(self, uid: str, updates: Dict[str, Any]) -> bool:
        """Update Firebase user"""
        try:
            self.auth_client.update_user(uid, **updates)
            return True
        except Exception as e:
            logger.error(f"Failed to update Firebase user: {str(e)}")
            return False
    
    async def delete_user(self, uid: str) -> bool:
        """Delete Firebase user"""
        try:
            self.auth_client.delete_user(uid)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Firebase user: {str(e)}")
            return False
    
    # File Storage Methods
    async def upload_file(self, file_path: str, file_content: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
        """Upload file to Firebase Storage"""
        try:
            bucket = self.storage_client.bucket()
            blob = bucket.blob(file_path)
            
            # Upload file
            blob.upload_from_string(file_content, content_type=content_type)
            
            # Make file publicly readable (optional)
            blob.make_public()
            
            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload file to Firebase Storage: {str(e)}")
            return None
    
    async def download_file(self, file_path: str) -> Optional[bytes]:
        """Download file from Firebase Storage"""
        try:
            bucket = self.storage_client.bucket()
            blob = bucket.blob(file_path)
            
            if blob.exists():
                return blob.download_as_bytes()
            return None
        except Exception as e:
            logger.error(f"Failed to download file from Firebase Storage: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Firebase Storage"""
        try:
            bucket = self.storage_client.bucket()
            blob = bucket.blob(file_path)
            
            if blob.exists():
                blob.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file from Firebase Storage: {str(e)}")
            return False
    
    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in Firebase Storage"""
        try:
            bucket = self.storage_client.bucket()
            blobs = bucket.list_blobs(prefix=prefix)
            
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "created": blob.time_created,
                    "updated": blob.updated,
                    "public_url": blob.public_url
                })
            
            return files
        except Exception as e:
            logger.error(f"Failed to list files in Firebase Storage: {str(e)}")
            return []
    
    # Firestore Methods
    async def create_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Create document in Firestore"""
        try:
            doc_ref = self.firestore_client.collection(collection).document(doc_id)
            doc_ref.set(data)
            return True
        except Exception as e:
            logger.error(f"Failed to create Firestore document: {str(e)}")
            return False
    
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document from Firestore"""
        try:
            doc_ref = self.firestore_client.collection(collection).document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get Firestore document: {str(e)}")
            return None
    
    async def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update document in Firestore"""
        try:
            doc_ref = self.firestore_client.collection(collection).document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            logger.error(f"Failed to update Firestore document: {str(e)}")
            return False
    
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete document from Firestore"""
        try:
            doc_ref = self.firestore_client.collection(collection).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete Firestore document: {str(e)}")
            return False
    
    async def query_documents(self, collection: str, filters: List[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Query documents from Firestore"""
        try:
            query = self.firestore_client.collection(collection)
            
            # Apply filters
            if filters:
                for filter_item in filters:
                    field = filter_item.get("field")
                    operator = filter_item.get("operator", "==")
                    value = filter_item.get("value")
                    query = query.where(field, operator, value)
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            
            results = []
            for doc in docs:
                results.append({"id": doc.id, **doc.to_dict()})
            
            return results
        except Exception as e:
            logger.error(f"Failed to query Firestore documents: {str(e)}")
            return []
    
    # User Profile Management in Firestore
    async def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Save user profile to Firestore"""
        profile_data["updated_at"] = datetime.now()
        return await self.create_document("user_profiles", user_id, profile_data)
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Firestore"""
        return await self.get_document("user_profiles", user_id)
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile in Firestore"""
        updates["updated_at"] = datetime.now()
        return await self.update_document("user_profiles", user_id, updates)
    
    # Conversation History in Firestore
    async def save_conversation(self, conversation_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Save conversation to Firestore"""
        conversation_data["updated_at"] = datetime.now()
        return await self.create_document("conversations", conversation_id, conversation_data)
    
    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user conversations from Firestore"""
        filters = [{"field": "user_id", "value": user_id}]
        return await self.query_documents("conversations", filters, limit)
    
    # Analytics in Firestore
    async def log_analytics_event(self, event_data: Dict[str, Any]) -> bool:
        """Log analytics event to Firestore"""
        event_data["timestamp"] = datetime.now()
        event_id = f"{event_data.get('user_id', 'anonymous')}_{int(datetime.now().timestamp())}"
        return await self.create_document("analytics", event_id, event_data)
    
    async def get_analytics_events(self, user_id: str = None, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get analytics events from Firestore"""
        filters = []
        
        if user_id:
            filters.append({"field": "user_id", "value": user_id})
        
        if event_type:
            filters.append({"field": "event_type", "value": event_type})
        
        return await self.query_documents("analytics", filters, limit)
    
    # Health Check
    async def health_check(self) -> Dict[str, bool]:
        """Check Firebase services health"""
        health_status = {
            "initialized": self.initialized,
            "auth": False,
            "storage": False,
            "firestore": False
        }
        
        if not self.initialized:
            return health_status
        
        try:
            # Test auth
            self.auth_client.get_user("test")
            health_status["auth"] = True
        except:
            pass
        
        try:
            # Test storage
            bucket = self.storage_client.bucket()
            bucket.list_blobs(max_results=1)
            health_status["storage"] = True
        except:
            pass
        
        try:
            # Test firestore
            self.firestore_client.collection("test").limit(1).get()
            health_status["firestore"] = True
        except:
            pass
        
        return health_status

# Global Firebase manager instance
firebase_manager = None

async def init_firebase(project_id: str, service_account_path: str = None) -> FirebaseManager:
    """Initialize Firebase manager"""
    global firebase_manager
    firebase_manager = FirebaseManager(project_id, service_account_path)
    await firebase_manager.initialize()
    return firebase_manager

async def get_firebase() -> FirebaseManager:
    """Get Firebase manager instance"""
    return firebase_manager
