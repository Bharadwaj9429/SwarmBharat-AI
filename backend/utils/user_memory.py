"""
SwarmBharat User Memory System
Permanent memory of user profiles, documents, and conversation history
This is what makes SwarmBharat your family advisor, not a stranger
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserDomain(str, Enum):
    """Domains user is interested in"""
    FARMING = "farming"
    CAREER = "career"
    IMMIGRATION = "immigration"
    FINANCE = "finance"
    HEALTH = "health"
    LEGAL = "legal"
    EDUCATION = "education"
    BUSINESS = "business"
    GOVERNMENT = "government"


class UserMode(str, Enum):
    """User expertise level - affects response style"""
    GUIDED = "guided"  # Hand-holding, simple language
    EXPERT = "expert"   # Direct answers, technical depth


class UserMemory:
    """
    Persistent user memory system
    Stores: profile info, documents, conversation history, goals, preferences
    
    In production, replace with Firestore/MongoDB
    For now using JSON file storage as fallback
    """
    
    def __init__(self, user_id: str, storage_path: str = "data/users"):
        self.user_id = user_id
        self.storage_path = storage_path
        self.file_path = os.path.join(storage_path, f"{user_id}.json")
        
        # Create directory if needed
        os.makedirs(storage_path, exist_ok=True)
        
        # Load or initialize
        self.profile = self._load_profile()
    
    def _load_profile(self) -> Dict[str, Any]:
        """Load user profile from storage"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Could not load profile for {self.user_id}: {str(e)}")
        
        # Initialize new profile
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "mode": UserMode.GUIDED.value,
            "language": "English",
            "profile_complete": False,
            
            # Personal info
            "personal": {
                "name": None,
                "age": None,
                "gender": None,
                "phone": None,
                "email": None,
                "city": None,
                "district": None,
                "state": None,
                "aadhaar_masked": None,
                "education": None
            },
            
            # Interests/domains
            "domains": [],
            "current_domain": None,
            "primary_challenge": None,
            
            # User type indicators
            "user_type": None,  # student, professional, farmer, business_owner, etc
            
            # Domain-specific info
            "farming": {
                "is_farmer": False,
                "farm_size_acres": None,
                "crops": [],
                "district": None,
                "schemes_interested": []
            },
            
            "career": {
                "current_role": None,
                "company": None,
                "experience_years": None,
                "target_role": None,
                "current_salary": None,
                "job_hunting": False,
                "skills": [],
                "certifications": []
            },
            
            "immigration": {
                "interested": False,
                "target_country": None,  # Canada, US, UK, Australia
                "education_level": None,
                "work_experience_years": None,
                "language_proficiency": None,
                "crs_score": None
            },
            
            "finance": {
                "annual_income": None,
                "monthly_expenses": None,
                "savings": None,
                "investments": [],
                "loans": [],
                "credit_score": None
            },
            
            "health": {
                "age_group": None,
                "conditions": [],
                "allergies": [],
                "medications": [],
                "insurance_type": None,
                "insurance_provider": None
            },
            
            # Preferences
            "preferences": {
                "response_length": "medium",  # short, medium, long
                "tone": "professional",  # friendly, professional, expert
                "include_data": True,
                "notifications_enabled": False
            },
            
            # Documents vault
            "documents": [],  # List of uploaded documents with metadata
            
            # Conversation history
            "conversations": [],  # Recent conversation summaries
            
            # Tracking
            "commitments": [],  # Things user said they'd do
            "action_tracker": [],  # Tracked actions with status
            "goals": [],  # User's stated goals
            
            # Community data (anonymized)
            "similar_users_count": 0,  # How many users have similar profile
            "success_rate_for_situation": 0  # % of similar users who succeeded
        }
    
    def _save_profile(self) -> bool:
        """Persist profile to storage"""
        try:
            self.profile["updated_at"] = datetime.now().isoformat()
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Could not save profile for {self.user_id}: {str(e)}")
            return False
    
    # =====================
    # Profile Building
    # =====================
    
    async def complete_onboarding(self, data: Dict[str, Any]) -> bool:
        """Save onboarding data - called after profile builder"""
        try:
            self.profile["personal"].update({
                "name": data.get("name"),
                "age": data.get("age"),
                "gender": data.get("gender"),
                "city": data.get("city"),
                "district": data.get("district"),
                "state": data.get("state"),
                "education": data.get("education")
            })
            
            self.profile["user_type"] = data.get("user_type")
            self.profile["domains"] = data.get("domains", [])
            self.profile["primary_challenge"] = data.get("primary_challenge")
            self.profile["language"] = data.get("language", "English")
            self.profile["mode"] = data.get("mode", UserMode.GUIDED.value)
            self.profile["profile_complete"] = True
            
            return self._save_profile()
        except Exception as e:
            logger.error(f"Onboarding failed: {str(e)}")
            return False
    
    async def update_domain_info(self, domain: str, info: Dict[str, Any]) -> bool:
        """Update domain-specific information"""
        try:
            if domain.lower() in self.profile:
                self.profile[domain.lower()].update(info)
            self._save_profile()
            return True
        except Exception as e:
            logger.error(f"Domain update failed: {str(e)}")
            return False
    
    # =====================
    # Memory Queries
    # =====================
    
    async def remember(self, key: str, value: Any, domain: str = None) -> bool:
        """
        Store a fact about the user permanently
        Examples:
        - await memory.remember("has_diabetes", True, "health")
        - await memory.remember("target_role", "ML Engineer", "career")
        - await memory.remember("wants_canada_pr", True, "immigration")
        """
        try:
            if domain and domain in self.profile:
                self.profile[domain][key] = value
            else:
                # Store in general personal section
                self.profile["personal"][key] = value
            
            self._save_profile()
            logger.info(f"✓ Remembered: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Remember failed: {str(e)}")
            return False
    
    async def recall(self, key: str, domain: str = None) -> Optional[Any]:
        """Retrieve a specific memory about the user"""
        try:
            if domain and domain in self.profile:
                return self.profile[domain].get(key)
            else:
                return self.profile["personal"].get(key)
        except Exception as e:
            logger.error(f"Recall failed: {str(e)}")
            return None
    
    async def get_all_memories(self) -> Dict[str, Any]:
        """Get all user memories as structured context"""
        memories = {
            "about_user": self.profile.get("personal", {}),
            "domains": self.profile.get("domains", []),
            "current_challenge": self.profile.get("primary_challenge"),
            "mode": self.profile.get("mode"),
            "language": self.profile.get("language")
        }
        
        # Add domain-specific data
        for domain in self.profile.get("domains", []):
            if domain in self.profile:
                memories[f"{domain}_info"] = self.profile[domain]
        
        return memories
    
    async def inject_into_prompt(self, current_query: str) -> str:
        """
        Generate context injection for prompts
        Every agent query gets this prepended
        """
        memories = await self.get_all_memories()
        personal = memories.get("about_user", {})
        
        context = f"""
=== USER CONTEXT (DO NOT REPEAT THESE QUESTIONS) ===
User: {personal.get('name', 'Friend')}
Location: {personal.get('city', '')} {personal.get('district', '')} {personal.get('state', '')}
Background: {personal.get('education', 'Not specified')}
Challenges: {memories.get('current_challenge', 'Not specified')}

=== WHAT YOU KNOW FROM PREVIOUS CONVERSATIONS ===
"""
        
        # Add domain-specific context
        for domain in memories.get("domains", []):
            context += f"\n{domain.upper()}:\n"
            domain_info = memories.get(f"{domain}_info", {})
            for key, value in domain_info.items():
                if value and key != "is_" + domain:
                    context += f"  • {key}: {value}\n"
        
        context += f"""

=== USER PREFERENCES ===
Response style: {memories.get('mode', 'guided')}
Language: {memories.get('language', 'English')}

=== CURRENT QUESTION ===
{current_query}

INSTRUCTIONS:
1. Use their known context to give personalised answers
2. Don't ask what they've already told you
3. Reference their specific situation, not generic advice
4. Remember their goals and build on them
5. If you discover NEW important info, suggest they save it to memory
"""
        return context
    
    # =====================
    # Document Management
    # =====================
    
    async def store_document(self, doc_name: str, doc_type: str, 
                            file_path: str, metadata: Dict[str, Any] = None) -> bool:
        """Store document reference in vault"""
        try:
            doc_record = {
                "name": doc_name,
                "type": doc_type,  # resume, certificate, report, aadhaar, etc
                "file_path": file_path,
                "uploaded_at": datetime.now().isoformat(),
                "metadata": metadata or {},
                "usage_count": 0
            }
            
            # Check if already exists
            existing = [d for d in self.profile["documents"] if d["name"] == doc_name]
            if existing:
                self.profile["documents"].remove(existing[0])
            
            self.profile["documents"].append(doc_record)
            self._save_profile()
            logger.info(f"✓ Document stored: {doc_name}")
            return True
        except Exception as e:
            logger.error(f"Document storage failed: {str(e)}")
            return False
    
    async def get_documents(self, doc_type: str = None) -> List[Dict[str, Any]]:
        """Get stored documents, optionally filtered by type"""
        docs = self.profile.get("documents", [])
        if doc_type:
            docs = [d for d in docs if d.get("type") == doc_type]
        return docs
    
    async def use_document(self, doc_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve document and increment usage counter"""
        try:
            for doc in self.profile["documents"]:
                if doc["name"] == doc_name:
                    doc["usage_count"] = doc.get("usage_count", 0) + 1
                    self._save_profile()
                    return doc
            return None
        except Exception as e:
            logger.error(f"Document retrieval failed: {str(e)}")
            return None
    
    # =====================
    # Action Tracking
    # =====================
    
    async def add_action_commitment(self, action: str, deadline: str = None, 
                                   domain: str = None) -> bool:
        """Track something user committed to do"""
        try:
            commitment = {
                "action": action,
                "deadline": deadline,
                "domain": domain,
                "created_at": datetime.now().isoformat(),
                "status": "pending",  # pending, done, skipped
                "reminder_sent": False
            }
            
            self.profile["commitments"].append(commitment)
            self._save_profile()
            logger.info(f"✓ Commitment tracked: {action}")
            return True
        except Exception as e:
            logger.error(f"Commitment tracking failed: {str(e)}")
            return False
    
    async def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all uncompleted commitments"""
        return [c for c in self.profile.get("commitments", []) 
                if c.get("status") == "pending"]
    
    async def mark_action_done(self, action: str) -> bool:
        """Mark a commitment as completed"""
        try:
            for commitment in self.profile.get("commitments", []):
                if commitment["action"] == action:
                    commitment["status"] = "done"
                    commitment["completed_at"] = datetime.now().isoformat()
                    self._save_profile()
                    logger.info(f"✓ Action marked done: {action}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Mark action failed: {str(e)}")
            return False
    
    # =====================
    # Analytics
    # =====================
    
    async def get_engagement_stats(self) -> Dict[str, Any]:
        """Get user engagement metrics"""
        return {
            "profile_complete": self.profile.get("profile_complete", False),
            "domains_interested": len(self.profile.get("domains", [])),
            "documents_stored": len(self.profile.get("documents", [])),
            "pending_actions": len(await self.get_pending_actions()),
            "completed_actions": len([c for c in self.profile.get("commitments", []) 
                                      if c.get("status") == "done"]),
            "conversations_count": len(self.profile.get("conversations", []))
        }
    
    async def get_user_profile_summary(self) -> str:
        """Get human-readable profile summary"""
        p = self.profile
        summary = f"""
SWARM BHARAT USER PROFILE
========================
User: {p['personal'].get('name', 'Anonymous')}
Location: {p['personal'].get('city')}, {p['personal'].get('district')}, {p['personal'].get('state')}
Mode: {p.get('mode').upper()}
Language: {p.get('language')}

INTERESTS:
{', '.join(p.get('domains', [])).title() if p.get('domains') else 'Not set'}

CHALLENGE:
{p.get('primary_challenge', 'Not specified')}

DOCUMENTS:
{len(p.get('documents', []))} files stored

PENDING ACTIONS:
{len(await self.get_pending_actions())} tasks
"""
        return summary


# Global memory instance per user
_memory_cache = {}

def get_user_memory(user_id: str) -> UserMemory:
    """Get or create user memory instance"""
    if user_id not in _memory_cache:
        _memory_cache[user_id] = UserMemory(user_id)
    return _memory_cache[user_id]
