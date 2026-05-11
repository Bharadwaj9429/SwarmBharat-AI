"""
Personalization Engine for SwarmBharat AI
Customizes responses based on user profile, context, and preferences
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class UserProfile:
    """User profile for personalization"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.basic_info = {}
        self.financial_profile = {}
        self.career_profile = {}
        self.preferences = {}
        self.interaction_history = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_basic_info(self, data: Dict[str, Any]):
        """Update basic user information"""
        self.basic_info.update(data)
        self.updated_at = datetime.now()
    
    def update_financial_profile(self, data: Dict[str, Any]):
        """Update financial information"""
        self.financial_profile.update(data)
        self.updated_at = datetime.now()
    
    def update_career_profile(self, data: Dict[str, Any]):
        """Update career information"""
        self.career_profile.update(data)
        self.updated_at = datetime.now()
    
    def update_preferences(self, data: Dict[str, Any]):
        """Update user preferences"""
        self.preferences.update(data)
        self.updated_at = datetime.now()
    
    def add_interaction(self, query: str, domain: str, response_quality: int = None):
        """Add interaction to history"""
        self.interaction_history.append({
            "query": query,
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "response_quality": response_quality
        })
        self.updated_at = datetime.now()
    
    def get_personalization_context(self) -> Dict[str, Any]:
        """Get full context for personalization"""
        return {
            "user_id": self.user_id,
            "basic_info": self.basic_info,
            "financial_profile": self.financial_profile,
            "career_profile": self.career_profile,
            "preferences": self.preferences,
            "recent_domains": self._get_recent_domains(),
            "interaction_count": len(self.interaction_history),
            "avg_response_quality": self._get_avg_quality()
        }
    
    def _get_recent_domains(self, limit: int = 5) -> List[str]:
        """Get recently interacted domains"""
        recent = self.interaction_history[-limit:] if self.interaction_history else []
        return list(set([item["domain"] for item in recent]))
    
    def _get_avg_quality(self) -> Optional[float]:
        """Get average response quality rating"""
        qualities = [item["response_quality"] for item in self.interaction_history 
                    if item.get("response_quality") is not None]
        return sum(qualities) / len(qualities) if qualities else None

class PersonalizationEngine:
    """Engine for personalizing AI responses"""
    
    def __init__(self):
        self.profiles = {}  # In-memory storage, replace with DB in production
        self.personalization_rules = self._load_personalization_rules()
    
    def _load_personalization_rules(self) -> Dict[str, Any]:
        """Load personalization rules for different contexts"""
        return {
            "investment": {
                "age_based_adjustments": {
                    "18-25": {
                        "tone": "educational",
                        "risk_focus": "long_term_growth",
                        "examples": "student_friendly",
                        "complexity": "simple"
                    },
                    "26-35": {
                        "tone": "practical",
                        "risk_focus": "balanced_growth",
                        "examples": "young_professional",
                        "complexity": "moderate"
                    },
                    "36-50": {
                        "tone": "strategic",
                        "risk_focus": "wealth_preservation",
                        "examples": "family_focused",
                        "complexity": "detailed"
                    },
                    "51+": {
                        "tone": "conservative",
                        "risk_focus": "retirement_focused",
                        "examples": "senior_friendly",
                        "complexity": "simple"
                    }
                },
                "income_based_adjustments": {
                    "low": {"amount_examples": "small_amounts", "focus": "savings_first"},
                    "medium": {"amount_examples": "moderate_amounts", "focus": "balanced_approach"},
                    "high": {"amount_examples": "large_amounts", "focus": "optimization"}
                },
                "location_specific": {
                    "Maharashtra": {"mention": "Maharashtra-specific schemes", "examples": "Mumbai, Pune"},
                    "Karnataka": {"mention": "Karnataka-specific schemes", "examples": "Bangalore"},
                    "Tamil Nadu": {"mention": "Tamil Nadu-specific schemes", "examples": "Chennai"},
                    "Delhi": {"mention": "Delhi-specific schemes", "examples": "NCR region"}
                }
            },
            "career": {
                "experience_based": {
                    "fresher": {"focus": "skill_building", "advice": "entry_level"},
                    "1-3_years": {"focus": "growth", "advice": "early_career"},
                    "3-7_years": {"focus": "specialization", "advice": "mid_career"},
                    "7+_years": {"focus": "leadership", "advice": "senior_level"}
                },
                "industry_specific": {
                    "IT": {"trends": "tech_trends", "skills": "programming_skills"},
                    "Finance": {"trends": "fintech_trends", "skills": "analytical_skills"},
                    "Healthcare": {"trends": "healthcare_trends", "skills": "medical_skills"},
                    "Education": {"trends": "edtech_trends", "skills": "teaching_skills"}
                }
            }
        }
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one"""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(user_id)
        return self.profiles[user_id]
    
    def personalize_query(self, query: str, domain: str, user_id: str) -> Dict[str, Any]:
        """Add personalization context to query"""
        profile = self.get_or_create_profile(user_id)
        context = profile.get_personalization_context()
        
        # Add interaction to history
        profile.add_interaction(query, domain)
        
        # Generate personalization prompts
        personalization_prompts = self._generate_personalization_prompts(
            query, domain, context
        )
        
        return {
            "original_query": query,
            "personalized_query": self._enhance_query_with_context(query, domain, context),
            "context": context,
            "personalization_prompts": personalization_prompts,
            "response_modifiers": self._get_response_modifiers(domain, context)
        }
    
    def _generate_personalization_prompts(self, query: str, domain: str, context: Dict[str, Any]) -> List[str]:
        """Generate personalization prompts for AI"""
        prompts = []
        
        # Age-based personalization
        age = context["basic_info"].get("age")
        if age and domain in self.personalization_rules:
            age_group = self._get_age_group(age)
            if age_group in self.personalization_rules[domain]["age_based_adjustments"]:
                rules = self.personalization_rules[domain]["age_based_adjustments"][age_group]
                prompts.append(f"Use a {rules['tone']} tone suitable for someone aged {age}")
                prompts.append(f"Focus on {rules['risk_focus']} and use {rules['examples']} examples")
                prompts.append(f"Keep complexity {rules['complexity']}")
        
        # Location-based personalization
        location = context["basic_info"].get("state")
        if location and domain in self.personalization_rules:
            location_rules = self.personalization_rules[domain].get("location_specific", {}).get(location, {})
            if location_rules:
                prompts.append(f"Mention {location_rules.get('mention', 'relevant local information')}")
                if "examples" in location_rules:
                    prompts.append(f"Use examples from {location_rules['examples']}")
        
        # Income-based personalization
        income = context["financial_profile"].get("monthly_income")
        if income and domain == "investment":
            income_category = self._get_income_category(income)
            if income_category in self.personalization_rules[domain]["income_based_adjustments"]:
                rules = self.personalization_rules[domain]["income_based_adjustments"][income_category]
                prompts.append(f"Focus on {rules['focus']} with {rules['amount_examples']}")
        
        # Career-specific personalization
        if domain == "career":
            experience = context["career_profile"].get("years_experience")
            if experience:
                exp_category = self._get_experience_category(experience)
                if exp_category in self.personalization_rules[domain]["experience_based"]:
                    rules = self.personalization_rules[domain]["experience_based"][exp_category]
                    prompts.append(f"Focus on {rules['focus']} with {rules['advice']} advice")
        
        # Language preference
        language = context["preferences"].get("language", "English")
        if language != "English":
            prompts.append(f"Respond in {language} when possible, use simple terms")
        
        # Risk tolerance
        risk_tolerance = context["financial_profile"].get("risk_tolerance")
        if risk_tolerance and domain in ["investment", "business"]:
            prompts.append(f"Consider {risk_tolerance} risk tolerance in recommendations")
        
        return prompts
    
    def _enhance_query_with_context(self, query: str, domain: str, context: Dict[str, Any]) -> str:
        """Enhance query with user context"""
        enhanced_query = query
        
        # Add context information
        context_info = []
        
        if context["basic_info"].get("age"):
            context_info.append(f"User is {context['basic_info']['age']} years old")
        
        if context["basic_info"].get("state"):
            context_info.append(f"Located in {context['basic_info']['state']}")
        
        if context["financial_profile"].get("monthly_income"):
            context_info.append(f"Monthly income: ₹{context['financial_profile']['monthly_income']}")
        
        if context["career_profile"].get("current_role"):
            context_info.append(f"Current role: {context['career_profile']['current_role']}")
        
        if context["financial_profile"].get("risk_tolerance"):
            context_info.append(f"Risk tolerance: {context['financial_profile']['risk_tolerance']}")
        
        if context_info:
            enhanced_query = f"""
User Context: {', '.join(context_info)}

Original Query: {query}

Please provide a response that is specifically tailored to this user's situation, not generic advice.
"""
        
        return enhanced_query
    
    def _get_response_modifiers(self, domain: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get response modifications based on user context"""
        modifiers = {
            "tone": "professional",
            "complexity": "moderate",
            "examples": "general",
            "length": "detailed"
        }
        
        # Age-based modifications
        age = context["basic_info"].get("age")
        if age:
            age_group = self._get_age_group(age)
            if age_group == "18-25":
                modifiers.update({
                    "tone": "friendly_mentor",
                    "complexity": "simple",
                    "examples": "relatable_young"
                })
            elif age_group == "51+":
                modifiers.update({
                    "tone": "respectful_expert",
                    "complexity": "simple",
                    "examples": "traditional"
                })
        
        # Experience-based modifications
        if domain == "career":
            experience = context["career_profile"].get("years_experience", 0)
            if experience < 1:
                modifiers["tone"] = "encouraging_guide"
            elif experience > 7:
                modifiers["tone"] = "peer_consultant"
        
        # Income-based modifications
        income = context["financial_profile"].get("monthly_income", 0)
        if income < 30000:
            modifiers["examples"] = "budget_friendly"
        elif income > 100000:
            modifiers["examples"] = "premium_options"
        
        return modifiers
    
    def _get_age_group(self, age: int) -> str:
        """Get age group category"""
        if age < 26:
            return "18-25"
        elif age < 36:
            return "26-35"
        elif age < 51:
            return "36-50"
        else:
            return "51+"
    
    def _get_income_category(self, income: int) -> str:
        """Get income category"""
        if income < 30000:
            return "low"
        elif income < 80000:
            return "medium"
        else:
            return "high"
    
    def _get_experience_category(self, years: float) -> str:
        """Get experience category"""
        if years < 1:
            return "fresher"
        elif years < 3:
            return "1-3_years"
        elif years < 7:
            return "3-7_years"
        else:
            return "7+_years"
    
    def update_profile_from_feedback(self, user_id: str, query: str, domain: str, feedback: Dict[str, Any]):
        """Update user profile based on feedback"""
        profile = self.get_or_create_profile(user_id)
        
        # Update interaction with feedback
        if "rating" in feedback:
            # Find the interaction and update rating
            for interaction in reversed(profile.interaction_history):
                if interaction["query"] == query and interaction["domain"] == domain:
                    interaction["response_quality"] = feedback["rating"]
                    break
        
        # Update preferences based on feedback
        if "preferred_tone" in feedback:
            profile.update_preferences({"preferred_tone": feedback["preferred_tone"]})
        
        if "preferred_complexity" in feedback:
            profile.update_preferences({"preferred_complexity": feedback["preferred_complexity"]})

# Global personalization engine instance
personalization_engine = PersonalizationEngine()
