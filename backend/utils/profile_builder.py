"""
SwarmBharat Profile Builder
Intelligent onboarding that captures user context in 2 minutes
This is how we never ask the same question twice
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfileBuilder:
    """
    Guides users through smart onboarding
    Skips irrelevant questions based on user type
    """
    
    DOMAINS = {
        "farming": {
            "display": "🌾 Farming & Agriculture",
            "questions": [
                "Are you a landowner farmer, tenant, or landless farm worker?",
                "How many acres do you farm?",
                "What crops do you grow?",
                "Which district/state is your farm in?",
                "Are you interested in government schemes like Rythu Bandhu, PM Kisan?",
                "Do you need help with weather forecasts, crop planning, or market prices?"
            ]
        },
        "career": {
            "display": "💼 Career & Jobs",
            "questions": [
                "Are you a student, working professional, or job seeker?",
                "What's your current role/company?",
                "How many years of experience do you have?",
                "What's your current salary range (if comfortable)?",
                "What role/salary are you targeting?",
                "Are you actively job hunting?"
            ]
        },
        "immigration": {
            "display": "✈️ Immigration & Visa",
            "questions": [
                "Are you interested in moving to another country?",
                "Which country interests you most? (Canada, USA, UK, Australia, others)",
                "What's your education level?",
                "How many years of work experience do you have?",
                "What's your English proficiency level?",
                "Do you have a job offer or sponsorship lined up?"
            ]
        },
        "finance": {
            "display": "💰 Finance & Investing",
            "questions": [
                "What's your annual household income (approx)?",
                "Are you interested in loans, investments, taxes, or overall planning?",
                "Do you have any current loans (education, home, business)?",
                "Are you interested in government schemes or benefits?",
                "Do you have health/life insurance?",
                "What's your risk tolerance for investments?"
            ]
        },
        "health": {
            "display": "🏥 Health & Medical",
            "questions": [
                "What's your age group?",
                "Do you have any existing health conditions?",
                "Are you interested in government health schemes like Ayushman Bharat?",
                "What type of health insurance do you have?",
                "Are you looking for mental health support, fitness, or specific treatment?"
            ]
        },
        "education": {
            "display": "📚 Education & Learning",
            "questions": [
                "Are you a student or parent looking for education guidance?",
                "What's your current education level?",
                "Are you interested in exams, courses, certifications, or career planning?",
                "Which field of study interests you?",
                "Are you preparing for competitive exams?"
            ]
        },
        "business": {
            "display": "🏢 Business & Entrepreneurship",
            "questions": [
                "Are you starting a new business or already running one?",
                "What sector/industry is your business in?",
                "How many employees do you have (or plan to have)?",
                "Do you need help with registration, compliance, funding, or growth?",
                "Are you interested in government schemes for entrepreneurs?"
            ]
        },
        "legal": {
            "display": "⚖️ Legal & Compliance",
            "questions": [
                "What legal issue are you facing? (property, contract, dispute, compliance)",
                "Do you already have a lawyer?",
                "Is this urgent (deadline soon)?",
                "Is this for personal, business, or property matter?",
                "Do you need help understanding laws or taking action?"
            ]
        },
        "government": {
            "display": "🏛️ Government Schemes & Benefits",
            "questions": [
                "What schemes are you curious about? (farmer, student, business, health, etc)",
                "What's your income level? (helps match you to right schemes)",
                "Do you have a specific concern? (land, taxes, registration, etc)",
                "Have you already applied for any schemes?",
                "Do you need help with application or verification?"
            ]
        }
    }
    
    USER_TYPES = {
        "student": {
            "display": "👤 Student/Fresher",
            "description": "Studying or just graduating",
            "relevant_domains": ["career", "education", "immigration", "finance"]
        },
        "working_professional": {
            "display": "👨‍💼 Working Professional",
            "description": "Currently employed, looking to grow",
            "relevant_domains": ["career", "finance", "immigration", "business"]
        },
        "business_owner": {
            "display": "🏢 Business Owner/Self-Employed",
            "description": "Running own business",
            "relevant_domains": ["business", "finance", "legal", "government"]
        },
        "farmer": {
            "display": "👨‍🌾 Farmer",
            "description": "Agriculture-focused",
            "relevant_domains": ["farming", "finance", "health", "government"]
        },
        "parent": {
            "display": "👨‍👩‍👧 Parent",
            "description": "Managing family",
            "relevant_domains": ["education", "finance", "health", "government"]
        },
        "homemaker": {
            "display": "👩‍🍳 Homemaker",
            "description": "Managing household",
            "relevant_domains": ["finance", "health", "education", "government"]
        },
        "retired": {
            "display": "🧓 Retired/Senior",
            "description": "Post-retirement",
            "relevant_domains": ["finance", "health", "legal", "government"]
        },
        "job_seeker": {
            "display": "🔍 Job Seeker",
            "description": "Currently looking for work",
            "relevant_domains": ["career", "finance", "education"]
        }
    }
    
    CITIES = {
        "Telangana": ["Hyderabad", "Secunderabad", "Warangal", "Vijayawada", "Karimnagar", "Nizamabad"],
        "Andhra Pradesh": ["Vijayawada", "Visakhapatnam", "Tirupati", "Guntur", "Rajahmundry"],
        "Karnataka": ["Bangalore", "Mysore", "Mangalore", "Belgaum", "Davangere"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Aurangabad", "Nashik"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruppur"],
        "National": ["All India", "Other"]
    }
    
    def __init__(self):
        self.current_step = 0
        self.profile_data = {}
        self.total_steps = 10  # Total onboarding steps
    
    def get_greeting_message(self) -> str:
        """First message to new user"""
        return """
👋 Welcome to SwarmBharat AI!

In just 2 minutes, I'll understand your situation so I can give you personalized advice - not generic answers.

Let's start with basics about you.
        """
    
    def get_step_1_user_type(self) -> Dict[str, Any]:
        """Step 1: Understand user type"""
        return {
            "step": 1,
            "title": "What's your current situation?",
            "type": "single_choice",
            "options": [option["display"] for option in self.USER_TYPES.values()],
            "hint": "This helps us focus on what matters to you"
        }
    
    def get_step_2_location(self) -> Dict[str, Any]:
        """Step 2: Get location"""
        all_cities = []
        for state, cities in self.CITIES.items():
            all_cities.extend(cities)
        
        return {
            "step": 2,
            "title": "Where are you located?",
            "type": "searchable_choice",
            "options": all_cities,
            "hint": "So I can give location-specific advice (schemes, job markets, etc)"
        }
    
    def get_step_3_primary_challenge(self) -> Dict[str, Any]:
        """Step 3: What's their main challenge?"""
        return {
            "step": 3,
            "title": "What's your biggest challenge right now?",
            "type": "open_text",
            "placeholder": "e.g., 'Stuck in current job', 'Afraid my payment won't come', 'Want to immigrate'",
            "hint": "Be specific - this is what we'll focus on"
        }
    
    def get_step_4_domains(self, user_type: str) -> Dict[str, Any]:
        """Step 4: Select interest areas (smart based on user type)"""
        
        # Get relevant domains for this user type
        if user_type in self.USER_TYPES:
            relevant = self.USER_TYPES[user_type]["relevant_domains"]
        else:
            relevant = list(self.DOMAINS.keys())
        
        relevant_options = {k: v for k, v in self.DOMAINS.items() if k in relevant}
        
        return {
            "step": 4,
            "title": "What areas interest you most?",
            "type": "multi_choice",
            "options": [f"{v['display']}" for v in relevant_options.values()],
            "hint": "Select all that apply",
            "min_select": 1,
            "max_select": 3
        }
    
    def get_step_5_mode_preference(self) -> Dict[str, Any]:
        """Step 5: Guided vs Expert mode"""
        return {
            "step": 5,
            "title": "How would you like guidance?",
            "type": "single_choice",
            "options": [
                "🎓 Guided - Hand-holding, explain everything, step-by-step",
                "🚀 Expert - Direct answers, assume I know the basics"
            ],
            "hint": "You can change this anytime"
        }
    
    def get_step_6_language(self) -> Dict[str, Any]:
        """Step 6: Preferred language"""
        return {
            "step": 6,
            "title": "Preferred language?",
            "type": "single_choice",
            "options": ["English", "हिंदी (Hindi)", "తెలుగు (Telugu)"],
            "hint": "You can mix languages anytime"
        }
    
    def get_step_7_documents(self) -> Dict[str, Any]:
        """Step 7: Upload any relevant documents"""
        return {
            "step": 7,
            "title": "Got any documents I should know about?",
            "type": "file_upload",
            "accepted_files": ["pdf", "doc", "docx", "jpg", "png", "xlsx", "csv"],
            "optional": True,
            "hint": "Resume, medical reports, property deeds, bank statements, etc. I'll remember them."
        }
    
    def get_step_8_contact(self) -> Dict[str, Any]:
        """Step 8: Contact info"""
        return {
            "step": 8,
            "title": "How can I reach you?",
            "type": "form",
            "fields": {
                "name": {"type": "text", "placeholder": "Your name", "required": True},
                "phone": {"type": "tel", "placeholder": "9XXXXXXXXX", "required": False},
                "email": {"type": "email", "placeholder": "your@email.com", "required": False}
            },
            "hint": "For reminders and notifications"
        }
    
    def get_step_9_summary(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Step 9: Show summary for confirmation"""
        return {
            "step": 9,
            "title": "Here's what I know about you 👤",
            "type": "display",
            "summary": f"""
USER: {profile.get('name', 'Friend')}
LOCATION: {profile.get('city', 'Not specified')}
TYPE: {profile.get('user_type', 'Not specified')}
CHALLENGE: {profile.get('primary_challenge', 'Not specified')}
INTERESTS: {', '.join(profile.get('domains', [])).title() if profile.get('domains') else 'Not specified'}
MODE: {profile.get('mode', 'Guided')}
LANGUAGE: {profile.get('language', 'English')}

This means I won't ask these questions again. I'll build everything around YOUR situation.
            """,
            "action": "Confirm & Continue?"
        }
    
    def get_step_10_ready(self) -> Dict[str, Any]:
        """Step 10: Ready to start"""
        return {
            "step": 10,
            "title": "Perfect! Let's get started! 🚀",
            "type": "display",
            "message": """
I'm ready to help you. Here's how we work:

1️⃣ ASK - You ask anything about your situation
2️⃣ LEARN - I give real, specific advice (not generic ChatGPT stuff)
3️⃣ PLAN - We build a concrete action plan together
4️⃣ TRACK - I remind you about your commitments
5️⃣ CELEBRATE - When you win, we celebrate together 🎉

You can ask me about:
✓ Government schemes in your area
✓ Job opportunities matching your profile
✓ Financial planning for your situation
✓ Health/legal/farming/immigration advice
✓ Step-by-step action plans

Ready? What's on your mind today?
            """,
            "action": "Let's go! 🚀"
        }
    
    def save_profile_data(self, field: str, value: Any) -> bool:
        """Save profile field"""
        try:
            self.profile_data[field] = value
            logger.info(f"✓ Profile saved: {field} = {value}")
            return True
        except Exception as e:
            logger.error(f"Could not save profile: {str(e)}")
            return False
    
    def get_profile_data(self) -> Dict[str, Any]:
        """Get collected profile data"""
        return self.profile_data
    
    def get_onboarding_progress(self) -> Dict[str, Any]:
        """Get current progress"""
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percent": int((self.current_step / self.total_steps) * 100),
            "profile_complete": self.current_step >= self.total_steps
        }


# Quick-start profiles for testing/demo
QUICK_PROFILES = {
    "farmer": {
        "name": "Lakshmi",
        "user_type": "farmer",
        "city": "Nalgonda",
        "domains": ["farming", "finance", "government"],
        "mode": "guided",
        "language": "Telugu",
        "primary_challenge": "Payment from Rythu Bandhu didn't come"
    },
    "professional": {
        "name": "Karthik",
        "user_type": "working_professional",
        "city": "Hyderabad",
        "domains": ["career", "finance", "immigration"],
        "mode": "expert",
        "language": "English",
        "primary_challenge": "Stuck at current salary, want ML role"
    },
    "student": {
        "name": "Ravi",
        "user_type": "student",
        "city": "Bangalore",
        "domains": ["education", "career", "finance"],
        "mode": "guided",
        "language": "English",
        "primary_challenge": "What should I do after graduation?"
    }
}
