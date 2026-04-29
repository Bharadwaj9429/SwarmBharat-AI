"""
Firebase Client for SwarmBharat AI
Production-ready Firebase integration for authentication and storage
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class FirebaseClient:
    """
    Firebase client for SwarmBharat AI
    Free tier: 1GB storage, 50k reads/writes per day
    """
    
    def __init__(self):
        self.project_id = os.getenv("FIREBASE_PROJECT_ID")
        self.private_key_id = os.getenv("FIREBASE_PRIVATE_KEY_ID")
        self.app = None
        self.auth = None
        self.firestore = None
        self.storage = None
        self.connected = False
        
    async def connect(self):
        """Connect to Firebase"""
        try:
            if not FIREBASE_AVAILABLE:
                logger.warning("Firebase not installed, skipping Firebase integration")
                return False
                
            if not self.project_id:
                logger.warning("Firebase project ID not provided, skipping Firebase integration")
                return False
            
            # For development, we'll use a mock service account
            # In production, you'd use a real service account JSON file
            cred = credentials.ApplicationDefault()
            
            self.app = firebase_admin.initialize_app(cred, {
                'projectId': self.project_id,
            }, name='swarmbharat-ai')
            
            self.auth = auth.Client(self.app)
            self.firestore = firestore.Client(self.app)
            self.storage = storage.bucket(self.app)
            
            self.connected = True
            logger.info("✅ Connected to Firebase")
            return True
            
        except Exception as e:
            logger.error(f"Firebase connection failed: {str(e)}")
            return False
    
    async def create_user(self, email: str, password: str, display_name: str = None) -> Optional[str]:
        """Create Firebase user"""
        try:
            if not self.connected:
                return None
                
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            
            logger.info(f"Created Firebase user: {user.uid}")
            return user.uid
            
        except Exception as e:
            logger.error(f"Failed to create Firebase user: {str(e)}")
            return None
    
    async def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token"""
        try:
            if not self.connected:
                return None
                
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
            
        except Exception as e:
            logger.error(f"Failed to verify Firebase token: {str(e)}")
            return None
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get Firebase user by UID"""
        try:
            if not self.connected:
                return None
                
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "email_verified": user.email_verified,
                "disabled": user.disabled
            }
            
        except Exception as e:
            logger.error(f"Failed to get Firebase user: {str(e)}")
            return None
    
    async def save_to_firestore(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Save document to Firestore"""
        try:
            if not self.connected:
                return False
                
            doc_ref = self.firestore.collection(collection).document(document_id)
            doc_ref.set({
                **data,
                "updated_at": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to Firestore: {str(e)}")
            return False
    
    async def get_from_firestore(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document from Firestore"""
        try:
            if not self.connected:
                return None
                
            doc_ref = self.firestore.collection(collection).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get from Firestore: {str(e)}")
            return None
    
    async def upload_file(self, file_data: bytes, file_name: str, content_type: str = "application/octet-stream") -> Optional[str]:
        """Upload file to Firebase Storage"""
        try:
            if not self.connected:
                return None
                
            blob = self.storage.blob(file_name)
            blob.upload_from_string(file_data, content_type=content_type)
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to Firebase Storage: {str(e)}")
            return None
    
    async def delete_file(self, file_name: str) -> bool:
        """Delete file from Firebase Storage"""
        try:
            if not self.connected:
                return False
                
            blob = self.storage.blob(file_name)
            blob.delete()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from Firebase Storage: {str(e)}")
            return False
    
    async def query_firestore(self, collection: str, filters: List[tuple] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query Firestore with optional filters"""
        try:
            if not self.connected:
                return []
                
            query = self.firestore.collection(collection)
            
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            results = []
            
            for doc in docs:
                results.append({
                    "id": doc.id,
                    **doc.to_dict()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query Firestore: {str(e)}")
            return []
    
    async def update_firestore(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Update document in Firestore"""
        try:
            if not self.connected:
                return False
                
            doc_ref = self.firestore.collection(collection).document(document_id)
            doc_ref.update({
                **data,
                "updated_at": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Firestore: {str(e)}")
            return False
    
    async def get_firestore_stats(self) -> Dict[str, Any]:
        """Get Firestore usage statistics"""
        try:
            if not self.connected:
                return {}
                
            # Get collection sizes
            collections = ['users', 'conversations', 'documents', 'user_memory']
            stats = {}
            
            for collection_name in collections:
                docs = self.firestore.collection(collection_name).limit(1).stream()
                count = len(list(docs))
                stats[f"{collection_name}_count"] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get Firestore stats: {str(e)}")
            return {}
    
    async def close(self):
        """Close Firebase connection"""
        if self.app:
            firebase_admin.delete_app(self.app)
            logger.info("Firebase connection closed")

# Global Firebase instance
firebase_client = FirebaseClient()
