"""
SwarmBharat Situation Detector
Analyzes user's emotional state and urgency level
Adapts responses based on fear, urgency, confusion, or excitement
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Greeting patterns - check FIRST before any other classification
GREETINGS = [
    'hello', 'hi', 'hey', 'namaste', 'hii', 'helo', 'helloo',
    'good morning', 'good evening', 'good afternoon', 'good night',
    'sup', 'wassup', 'hola', 'vanakkam', 'namaskar', 'kem cho',
    'sat sri akal', 'jai hind', 'howdy', 'greetings'
]


class SituationDetector:
    """
    Detects emotional and situational context from user messages
    Makes responses feel genuinely empathetic
    """
    
    # Emotional indicators (multi-language support)
    FEAR_INDICATORS = {
        "en": ["scared", "worried", "nervous", "afraid", "anxious", "panic", "terrified",
               "don't know", "confused", "lost", "stuck", "help"],
        "hi": ["डर", "चिंतित", "घबराया", "सहायता", "समझ नहीं", "भ्रमित", "अकेला"],
        "te": ["భయం", "చిందించిన", "ఆందోళన", "సహాయం", "అర్థం", "తెలియక", "ఒంటరి"]
    }
    
    URGENCY_INDICATORS = {
        "en": ["deadline", "last date", "expiring", "court", "eviction", "termination",
               "tomorrow", "today", "urgent", "asap", "immediately", "hurry", "police"],
        "hi": ["तारीख", "अंतिम", "कोर्ट", "आज", "कल", "तुरंत", "जल्दी"],
        "te": ["తేదీ", "చివరి", "కోర్టు", "ఈ రోజు", "రేపు", "తక్షణం", "తొందర"]
    }
    
    EXCITEMENT_INDICATORS = {
        "en": ["great", "amazing", "excellent", "love this", "excited", "awesome", "perfect",
               "cannot wait", "yes!", "definitely", "absolutely"],
        "hi": ["बहुत", "शानदार", "प्यार", "उत्साह", "हाँ", "निश्चित"],
        "te": ["చక్కగా", "అద్భుతం", "ప్రేమ", "ఉత్సాహం", "అవును", "ఖచ్చితంగా"]
    }
    
    CONFUSION_INDICATORS = {
        "en": ["what does this mean", "explain", "how does this work", "don't understand",
               "confusing", "complicated", "confused", "clarity", "meaning", "mean"],
        "hi": ["क्या मतलब", "समझाओ", "कैसे", "नहीं समझ", "भ्रमित", "जटिल"],
        "te": ["ఏమిటి అర్థం", "వివరించు", "ఎలా", "అర్థం కాలేదు", "బాధించేది", "కష్టం"]
    }
    
    FRUSTRATION_INDICATORS = {
        "en": ["frustrated", "angry", "upset", "annoyed", "fed up", "sick of", "hate",
               "why", "impossible", "broken", "failed"],
        "hi": ["निराश", "क्रोधी", "परेशान", "बीमार", "असंभव", "विफल"],
        "te": ["నిరాశ", "కోపం", "బాధపడిన", "అసాధ్యం", "విఫలమైన"]
    }
    
    GRATITUDE_INDICATORS = {
        "en": ["thank you", "thanks", "grateful", "appreciate", "wonderful", "helpful",
               "best", "saved", "lifesaver"],
        "hi": ["धन्यवाद", "कृतज्ञ", "सहायक", "सर्वश्रेष्ठ", "जीवन रक्षक"],
        "te": ["ధన్యవాదాలు", "కృతజ్ఞ", "సహాయకర", "ఉత్తమ", "జీవితరక్షక"]
    }
    
    def __init__(self):
        self.detected_emotions = {}
        self.user_emotional_trend = []  # Track emotion over multiple messages
    
    def detect_emotion(self, message: str, language: str = "en") -> Dict[str, Any]:
        """
        Analyze message for emotional indicators
        Returns dict with detected emotions and intensity
        """
        message_lower = message.lower()
        emotions = {}
        
        # Check each emotion type
        for emotion, indicators in [
            ("fear", self.FEAR_INDICATORS),
            ("urgency", self.URGENCY_INDICATORS),
            ("excitement", self.EXCITEMENT_INDICATORS),
            ("confusion", self.CONFUSION_INDICATORS),
            ("frustration", self.FRUSTRATION_INDICATORS),
            ("gratitude", self.GRATITUDE_INDICATORS)
        ]:
            lang_indicators = indicators.get(language, indicators.get("en", []))
            matches = sum(1 for ind in lang_indicators if ind.lower() in message_lower)
            
            if matches > 0:
                # Intensity: 0-100 based on number of matches
                intensity = min(100, matches * 20)
                emotions[emotion] = intensity
        
        return {
            "detected_emotions": emotions,
            "primary_emotion": max(emotions, key=emotions.get) if emotions else None,
            "intensity_score": max(emotions.values()) if emotions else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def detect_urgency(self, message: str, language: str = "en") -> Dict[str, Any]:
        """
        Specific urgency detection
        Returns: urgency_level (low, medium, high, critical)
        """
        message_lower = message.lower()
        urgency_indicators = self.URGENCY_INDICATORS.get(language, self.URGENCY_INDICATORS.get("en"))
        
        urgency_count = sum(1 for ind in urgency_indicators if ind.lower() in message_lower)
        
        # Check for critical keywords
        critical_keywords = ["police", "court", "deadline today", "expires today", "dying"]
        is_critical = any(keyword.lower() in message_lower for keyword in critical_keywords)
        
        if is_critical or urgency_count >= 3:
            level = "critical"
        elif urgency_count >= 2:
            level = "high"
        elif urgency_count == 1:
            level = "medium"
        else:
            level = "low"
        
        return {
            "urgency_level": level,
            "urgency_indicators_found": urgency_count,
            "is_critical": is_critical
        }
    
    def detect_user_type_from_context(self, message: str) -> Dict[str, Any]:
        """
        Infer user's situation from message content
        Even without explicit profile info
        """
        message_lower = message.lower()
        context = {}
        
        # Farmer context
        if any(word in message_lower for word in ["farm", "crop", "rainfall", "soil", "irrigation", 
                                                     "पेड़", "जमीन", "నేల", "పంట"]):
            context["likely_type"] = "farmer"
            context["confidence"] = 0.9
        
        # Job seeker
        elif any(word in message_lower for word in ["job", "resume", "salary", "interview", "company",
                                                      "नौकरी", "वेतन", "कंपनी", "ఉద్యోగం"]):
            context["likely_type"] = "job_seeker"
            context["confidence"] = 0.8
        
        # Student
        elif any(word in message_lower for word in ["exam", "college", "study", "degree", "course",
                                                      "परीक्षा", "कॉलेज", "पढाई", "డిగ్రీ"]):
            context["likely_type"] = "student"
            context["confidence"] = 0.8
        
        # Business owner
        elif any(word in message_lower for word in ["business", "startup", "profit", "revenue", "client",
                                                      "व्यापार", "स्टार्टअप", "मुनाफा", "వ్యాపారం"]):
            context["likely_type"] = "business_owner"
            context["confidence"] = 0.8
        
        # Immigration
        elif any(word in message_lower for word in ["visa", "immigration", "canada", "usa", "pr", "ircc",
                                                      "वीसा", "मूव", "कनाडा", "వీసా", "ఇమిగ్రేషన్"]):
            context["likely_type"] = "immigration_seeker"
            context["confidence"] = 0.9
        
        # Health
        elif any(word in message_lower for word in ["health", "doctor", "hospital", "medicine", "report",
                                                      "स्वास्थ्य", "डॉक्टर", "दवा", "ఆరోగ్య"]):
            context["likely_type"] = "health_seeker"
            context["confidence"] = 0.8
        
        else:
            context["likely_type"] = None
            context["confidence"] = 0
        
        return context
    
    def build_adaptive_response_plan(self, emotion_data: Dict[str, Any],
                                    urgency_data: Dict[str, Any],
                                    context_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Build response strategy based on detected situation
        """
        plan = {
            "tone": "neutral",
            "structure": "standard",
            "priority": "normal",
            "reassurance_needed": False,
            "action_focus": False,
            "detailed_explanation": False
        }
        
        primary_emotion = emotion_data.get("primary_emotion")
        urgency_level = urgency_data.get("urgency_level")
        
        # Adjust based on emotions
        if primary_emotion == "fear":
            plan["tone"] = "reassuring, empathetic"
            plan["reassurance_needed"] = True
            plan["structure"] = "reassure_first_then_inform"
        
        elif primary_emotion == "confusion":
            plan["tone"] = "patient, educational"
            plan["detailed_explanation"] = True
            plan["structure"] = "explain_then_guide"
        
        elif primary_emotion == "frustration":
            plan["tone"] = "solution-focused, action-oriented"
            plan["action_focus"] = True
            plan["structure"] = "acknowledge_then_fix"
        
        elif primary_emotion == "excitement":
            plan["tone"] = "encouraging, forward-looking"
            plan["structure"] = "validate_then_amplify"
        
        # Adjust based on urgency
        if urgency_level == "critical":
            plan["priority"] = "critical"
            plan["structure"] = "action_first_then_explain"
            plan["action_focus"] = True
        
        elif urgency_level == "high":
            plan["priority"] = "high"
            plan["action_focus"] = True
        
        return plan
    
    def get_reassurance_message(self, emotion: str, context: str = "") -> str:
        """
        Generate reassuring message based on detected fear/concern
        """
        reassurance_templates = {
            "fear": f"""
I understand you're worried. That's completely normal — many people face similar situations.
Here's the good news: {context or "This is actually solvable."} 

You're not alone. Let me walk you through this step by step. We'll figure it out together.
            """,
            
            "confusion": """
Don't worry — this stuff IS confusing when you encounter it first time. Let me break it down 
into simple parts. No stupid questions here.
            """,
            
            "frustration": """
I hear you. That's frustrating. Let's stop talking and start fixing it. Here's what we do:
            """,
            
            "urgency": """
I know time is tight. Let me cut through the noise and get straight to what matters.
Most important thing first:
            """
        }
        
        return reassurance_templates.get(emotion, "I'm here to help.")
    
    def get_response_modifiers(self, emotion_data: Dict[str, Any],
                              urgency_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get specific response modifications to apply
        """
        primary_emotion = emotion_data.get("primary_emotion")
        urgency_level = urgency_data.get("urgency_level")
        
        modifiers = {
            "prepend_reassurance": False,
            "include_examples": False,
            "include_step_by_step": False,
            "include_alternative_options": False,
            "include_resources": False,
            "include_timeline": False,
            "max_response_length": 300,
            "prioritize_action": False
        }
        
        # Based on fear
        if primary_emotion == "fear":
            modifiers["prepend_reassurance"] = True
            modifiers["include_examples"] = True
            modifiers["include_step_by_step"] = True
            modifiers["include_resources"] = True
            modifiers["max_response_length"] = 200
        
        # Based on confusion
        elif primary_emotion == "confusion":
            modifiers["include_examples"] = True
            modifiers["include_step_by_step"] = True
            modifiers["max_response_length"] = 400
        
        # Based on urgency
        if urgency_level == "critical":
            modifiers["prioritize_action"] = True
            modifiers["include_timeline"] = True
            modifiers["max_response_length"] = 150
        
        elif urgency_level == "high":
            modifiers["prioritize_action"] = True
            modifiers["include_timeline"] = True
        
        return modifiers
    
    def get_emotional_trend(self) -> Dict[str, Any]:
        """
        Analyze user's emotional trend over conversation
        Are they getting more confident? More worried?
        """
        if not self.user_emotional_trend:
            return {"status": "no_data"}
        
        recent = self.user_emotional_trend[-5:]  # Last 5 messages
        emotions_count = {}
        
        for emotion_record in recent:
            for emotion in emotion_record.get("detected_emotions", {}).keys():
                emotions_count[emotion] = emotions_count.get(emotion, 0) + 1
        
        return {
            "recent_emotions": emotions_count,
            "recent_message_count": len(recent),
            "trend": "improving" if emotions_count.get("gratitude", 0) > 2 else 
                    "declining" if emotions_count.get("frustration", 0) > 2 else "stable"
        }
    
    def analyze_document_emotion(self, doc_content: str) -> Dict[str, Any]:
        """
        Analyze uploaded documents for emotional context
        E.g., medical report → health concern, resume → career seeking
        """
        content_lower = doc_content.lower()
        
        analysis = {
            "document_type": None,
            "implied_situation": None,
            "emotional_context": None,
            "confidence": 0
        }
        
        # Medical document
        if any(word in content_lower for word in ["diagnosis", "treatment", "blood", "bp", "sugar", 
                                                    "medication", "patient", "hospital"]):
            analysis["document_type"] = "medical"
            analysis["implied_situation"] = "health_concern"
            analysis["emotional_context"] = "likely_anxious"
            analysis["confidence"] = 0.8
        
        # Resume/CV
        elif any(word in content_lower for word in ["experience", "skills", "education", "qualification",
                                                      "employment", "profile"]):
            analysis["document_type"] = "resume"
            analysis["implied_situation"] = "career_change"
            analysis["emotional_context"] = "likely_ambitious"
            analysis["confidence"] = 0.9
        
        # Property document
        elif any(word in content_lower for word in ["property", "registration", "deed", "survey",
                                                      "land", "aadhaar", "rao"]):
            analysis["document_type"] = "property"
            analysis["implied_situation"] = "property_transaction"
            analysis["emotional_context"] = "likely_cautious"
            analysis["confidence"] = 0.85
        
        # Bank/Finance
        elif any(word in content_lower for word in ["account", "balance", "loan", "emi", "interest",
                                                      "statement", "debit", "credit"]):
            analysis["document_type"] = "finance"
            analysis["implied_situation"] = "financial_planning"
            analysis["emotional_context"] = "likely_responsible"
            analysis["confidence"] = 0.8
        
        return analysis
    
    def detect_situation(self, message: str) -> dict:
        """
        Primary situation detection method - check greeting FIRST before any other logic
        """
        msg_clean = message.lower().strip().rstrip('!.,?')
        
        # GREETING CHECK — must be first before anything else
        if (msg_clean in GREETINGS or 
            any(msg_clean.startswith(g) for g in GREETINGS) or
            len(msg_clean.split()) <= 2 and any(g in msg_clean for g in GREETINGS)):
            return {
                "type": "greeting",
                "domain": None,
                "requires_tools": False,
                "requires_data_fetch": False,
                "requires_debate": False,
                "skip_action_tracker": True
            }
        
        # Fall back to existing detection logic
        emotion_data = self.detect_emotion(message)
        urgency_data = self.detect_urgency(message)
        context_data = self.detect_user_type_from_context(message)
        
        return {
            "type": "query",
            "domain": context_data.get("likely_type"),
            "requires_tools": True,
            "requires_data_fetch": True,
            "emotion": emotion_data,
            "urgency": urgency_data,
            "context": context_data
        }
