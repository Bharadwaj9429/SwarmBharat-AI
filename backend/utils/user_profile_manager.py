"""
User Profile Manager for SwarmBharat AI
Handles user onboarding, profile management, and personalization
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)

class UserProfileRequest(BaseModel):
    """Request model for user profile creation/update"""
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    # Basic Information
    age: int
    gender: str  # Male, Female, Other, Prefer not to say
    state: str  # Indian state
    city: str
    education: str  # High School, Graduate, Post Graduate, PhD, Other
    
    # Career Information
    employment_status: str  # Student, Employed, Self-employed, Freelancer, Unemployed, Retired
    industry: Optional[str] = None
    current_role: Optional[str] = None
    years_experience: Optional[float] = None
    monthly_income: Optional[int] = None
    company_name: Optional[str] = None
    
    # Financial Information
    risk_tolerance: str  # Conservative, Moderate, Aggressive
    investment_experience: str  # None, Beginner, Intermediate, Advanced
    financial_goals: List[str] = []  # Retirement, Home, Education, Business, Emergency Fund, etc.
    
    # Preferences
    language: str = "English"  # English, Hindi, Tamil, Telugu, Marathi, etc.
    preferred_tone: str = "Professional"  # Professional, Friendly, Casual
    notification_preferences: Dict[str, bool] = {}
    
    # Domain Interests
    domain_interests: List[str] = []  # Finance, Career, Health, Legal, Education, etc.

class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    user_id: str
    profile_completion: int
    created_at: str
    updated_at: str
    profile_data: Dict[str, Any]
    recommendations: List[str]

class UserProfileManager:
    """Manages user profiles and onboarding"""
    
    def __init__(self):
        self.profiles = {}  # In-memory storage, replace with database in production
        self.onboarding_steps = self._define_onboarding_steps()
    
    def _define_onboarding_steps(self) -> List[Dict[str, Any]]:
        """Define onboarding steps and their importance"""
        return [
            {
                "step": "basic_info",
                "title": "Basic Information",
                "description": "Tell us about yourself",
                "fields": ["age", "gender", "state", "city", "education"],
                "required": True,
                "weight": 30
            },
            {
                "step": "career_info",
                "title": "Career Information",
                "description": "Your professional background",
                "fields": ["employment_status", "industry", "current_role", "years_experience"],
                "required": True,
                "weight": 25
            },
            {
                "step": "financial_info",
                "title": "Financial Profile",
                "description": "Help us understand your financial situation",
                "fields": ["monthly_income", "risk_tolerance", "investment_experience", "financial_goals"],
                "required:": True,
                "weight": 25
            },
            {
                "step": "preferences",
                "title": "Preferences",
                "description": "Customize your experience",
                "fields": ["language", "preferred_tone", "domain_interests"],
                "required": False,
                "weight": 20
            }
        ]
    
    def create_or_update_profile(self, request: UserProfileRequest) -> UserProfileResponse:
        """Create or update user profile"""
        
        # Generate user_id if not provided
        user_id = request.user_id or str(uuid.uuid4())
        
        # Get existing profile or create new
        if user_id in self.profiles:
            profile = self.profiles[user_id]
            profile["updated_at"] = datetime.now().isoformat()
        else:
            profile = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "profile_data": {}
            }
        
        # Update profile data
        profile_data = profile["profile_data"]
        
        # Basic Information
        if request.age:
            profile_data["basic_info"] = {
                "age": request.age,
                "gender": request.gender,
                "state": request.state,
                "city": request.city,
                "education": request.education,
                "email": request.email,
                "phone": request.phone
            }
        
        # Career Information
        if any([request.employment_status, request.industry, request.current_role]):
            profile_data["career_profile"] = {
                "employment_status": request.employment_status,
                "industry": request.industry,
                "current_role": request.current_role,
                "years_experience": request.years_experience,
                "monthly_income": request.monthly_income,
                "company_name": request.company_name
            }
        
        # Financial Information
        if any([request.risk_tolerance, request.investment_experience, request.financial_goals]):
            profile_data["financial_profile"] = {
                "risk_tolerance": request.risk_tolerance,
                "investment_experience": request.investment_experience,
                "financial_goals": request.financial_goals or []
            }
        
        # Preferences
        if any([request.language, request.preferred_tone, request.domain_interests]):
            profile_data["preferences"] = {
                "language": request.language,
                "preferred_tone": request.preferred_tone,
                "notification_preferences": request.notification_preferences,
                "domain_interests": request.domain_interests or []
            }
        
        # Calculate profile completion
        completion = self._calculate_profile_completion(profile_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(profile_data, completion)
        
        # Save profile
        profile["profile_data"] = profile_data
        profile["profile_completion"] = completion
        self.profiles[user_id] = profile
        
        return UserProfileResponse(
            user_id=user_id,
            profile_completion=completion,
            created_at=profile["created_at"],
            updated_at=profile["updated_at"],
            profile_data=profile_data,
            recommendations=recommendations
        )
    
    def get_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """Get user profile"""
        if user_id not in self.profiles:
            return None
        
        profile = self.profiles[user_id]
        return UserProfileResponse(
            user_id=user_id,
            profile_completion=profile.get("profile_completion", 0),
            created_at=profile["created_at"],
            updated_at=profile["updated_at"],
            profile_data=profile["profile_data"],
            recommendations=self._generate_recommendations(profile["profile_data"], profile.get("profile_completion", 0))
        )
    
    def update_profile_partial(self, user_id: str, updates: Dict[str, Any]) -> UserProfileResponse:
        """Partially update user profile"""
        if user_id not in self.profiles:
            raise ValueError("User profile not found")
        
        profile = self.profiles[user_id]
        profile_data = profile["profile_data"]
        
        # Update specific sections
        for section, data in updates.items():
            if section in profile_data:
                profile_data[section].update(data)
            else:
                profile_data[section] = data
        
        profile["updated_at"] = datetime.now().isoformat()
        profile["profile_data"] = profile_data
        profile["profile_completion"] = self._calculate_profile_completion(profile_data)
        
        self.profiles[user_id] = profile
        
        return UserProfileResponse(
            user_id=user_id,
            profile_completion=profile["profile_completion"],
            created_at=profile["created_at"],
            updated_at=profile["updated_at"],
            profile_data=profile_data,
            recommendations=self._generate_recommendations(profile_data, profile["profile_completion"])
        )
    
    def _calculate_profile_completion(self, profile_data: Dict[str, Any]) -> int:
        """Calculate profile completion percentage"""
        total_weight = 0
        completed_weight = 0
        
        for step in self.onboarding_steps:
            step_weight = step["weight"]
            total_weight += step_weight
            
            # Check if required fields are completed
            required_fields = step["fields"]
            section_data = {}
            
            # Map step to profile section
            if step["step"] == "basic_info":
                section_data = profile_data.get("basic_info", {})
            elif step["step"] == "career_info":
                section_data = profile_data.get("career_profile", {})
            elif step["step"] == "financial_info":
                section_data = profile_data.get("financial_profile", {})
            elif step["step"] == "preferences":
                section_data = profile_data.get("preferences", {})
            
            # Count completed required fields
            completed_fields = 0
            for field in required_fields:
                if field in section_data and section_data[field]:
                    completed_fields += 1
            
            # Calculate step completion
            if step["required"]:
                step_completion = (completed_fields / len(required_fields)) * 100
            else:
                step_completion = (completed_fields / len(required_fields)) * 50  # Optional fields count less
            
            completed_weight += (step_completion / 100) * step_weight
        
        return int((completed_weight / total_weight) * 100) if total_weight > 0 else 0
    
    def _generate_recommendations(self, profile_data: Dict[str, Any], completion: int) -> List[str]:
        """Generate personalized recommendations based on profile"""
        recommendations = []
        
        if completion < 50:
            recommendations.append("Complete your profile to get personalized advice")
        
        # Age-based recommendations
        basic_info = profile_data.get("basic_info", {})
        age = basic_info.get("age")
        
        if age:
            if age < 25:
                recommendations.append("Focus on skill development and long-term growth")
                recommendations.append("Consider starting with small, regular investments")
            elif age < 35:
                recommendations.append("Balance career growth with financial planning")
                recommendations.append("Explore diversification in your investment portfolio")
            elif age < 50:
                recommendations.append("Focus on wealth preservation and retirement planning")
                recommendations.append("Consider tax optimization strategies")
            else:
                recommendations.append("Prioritize retirement income and healthcare planning")
                recommendations.append("Focus on low-risk, stable investments")
        
        # Career-based recommendations
        career = profile_data.get("career_profile", {})
        employment_status = career.get("employment_status")
        
        if employment_status == "Student":
            recommendations.append("Build skills that are in high demand in your chosen field")
            recommendations.append("Start learning about personal finance early")
        elif employment_status == "Employed":
            years_exp = career.get("years_experience", 0)
            if years_exp < 3:
                recommendations.append("Focus on gaining diverse experience and skills")
            else:
                recommendations.append("Consider specialization or leadership roles")
        
        # Financial-based recommendations
        financial = profile_data.get("financial_profile", {})
        risk_tolerance = financial.get("risk_tolerance")
        
        if risk_tolerance == "Conservative":
            recommendations.append("Focus on fixed deposits, PPF, and debt mutual funds")
        elif risk_tolerance == "Aggressive":
            recommendations.append("Consider equity mutual funds and growth stocks")
        else:
            recommendations.append("Maintain a balanced portfolio with both equity and debt")
        
        # Domain-specific recommendations
        preferences = profile_data.get("preferences", {})
        domain_interests = preferences.get("domain_interests", [])
        
        if "Finance" in domain_interests:
            recommendations.append("Explore our investment planning and tax optimization features")
        if "Career" in domain_interests:
            recommendations.append("Use our career guidance and skill development resources")
        if "Health" in domain_interests:
            recommendations.append("Check out our health insurance and wellness planning tools")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def get_onboarding_progress(self, user_id: str) -> Dict[str, Any]:
        """Get onboarding progress for user"""
        if user_id not in self.profiles:
            return {
                "completed_steps": 0,
                "total_steps": len(self.onboarding_steps),
                "progress_percentage": 0,
                "next_step": self.onboarding_steps[0] if self.onboarding_steps else None
            }
        
        profile = self.profiles[user_id]
        profile_data = profile["profile_data"]
        
        completed_steps = 0
        next_step = None
        
        for i, step in enumerate(self.onboarding_steps):
            # Check if step is completed
            section_data = {}
            if step["step"] == "basic_info":
                section_data = profile_data.get("basic_info", {})
            elif step["step"] == "career_info":
                section_data = profile_data.get("career_profile", {})
            elif step["step"] == "financial_info":
                section_data = profile_data.get("financial_profile", {})
            elif step["step"] == "preferences":
                section_data = profile_data.get("preferences", {})
            
            # Check required fields
            required_fields = step["fields"] if step["required"] else step["fields"][:2]  # For optional, check first 2
            completed_fields = sum(1 for field in required_fields if field in section_data and section_data[field])
            
            if completed_fields >= len(required_fields) * (0.8 if step["required"] else 0.5):
                completed_steps += 1
            elif next_step is None:
                next_step = step
        
        total_steps = len(self.onboarding_steps)
        progress_percentage = (completed_steps / total_steps) * 100
        
        return {
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "progress_percentage": int(progress_percentage),
            "next_step": next_step,
            "profile_completion": profile.get("profile_completion", 0)
        }
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        if user_id in self.profiles:
            del self.profiles[user_id]
            return True
        return False

# Global user profile manager instance
user_profile_manager = UserProfileManager()
