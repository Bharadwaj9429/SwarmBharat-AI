"""
SwarmBharat Conversation Engine
State machine for natural, human-like conversations
Transitions: greeting → understanding → deep_diving → action_planning → following_up
"""

from enum import Enum
from typing import Dict, Any, Tuple, List
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Conversation state machine"""
    GREETING = "greeting"           # First contact, warm introduction
    UNDERSTANDING = "understanding" # Asking clarifying questions
    DEEP_DIVING = "deep_diving"    # User engaged, going deeper
    ACTION_PLANNING = "action_planning"  # Building concrete steps
    FOLLOWING_UP = "following_up"   # Checking progress on previous commitments


class ConversationEngine:
    """
    Manages conversation flow and response formatting based on state
    Makes SwarmBharat feel like a consultant, not a chatbot
    """
    
    def __init__(self, user_mode: str = "guided"):
        """
        user_mode: 'guided' or 'expert'
        - guided: Hand-holding, simpler language, more questions
        - expert: Direct answers, technical depth, fewer questions
        """
        self.user_mode = user_mode
        self.current_state = ConversationState.GREETING
        self.turn_count = 0
        self.sessions = {}  # user_id -> message history
    
    def get_response_rules(self, state: ConversationState, user_mode: str) -> Dict[str, Any]:
        """
        Get formatting rules based on conversation state
        Controls: word limits, tone, structure, question emphasis
        """
        
        rules = {
            ConversationState.GREETING: {
                "max_words": 35 if user_mode == "guided" else 50,
                "must_end_with": "question",
                "tone": "warm, curious, human",
                "structure": [
                    "acknowledge_user",
                    "introduce_briefly",
                    "ask_one_clarifying_question"
                ],
                # Keep professional by default; let the client add emojis if desired.
                "emoji": False,
                "examples": {
                    "guided": "Hi there! 👋 Thanks for reaching out. I'm here to help you navigate [domain]. Before we dive in, what's the most pressing thing on your mind right now?",
                    "expert": "Hello. I'm ready to help with [domain]. What specific problem are we solving today?"
                }
            },
            
            ConversationState.UNDERSTANDING: {
                "max_words": 70 if user_mode == "guided" else 110,
                "must_end_with": "question",
                "tone": "focused, empathetic, professional",
                "structure": [
                    "validate_concern",
                    "reflect_back_what_they_said",
                    "ask_2_3_clarifying_questions",
                    "mention_next_steps"
                ],
                "questions_count": 3 if user_mode == "guided" else 2,
                "examples": {
                    "guided": "I understand — [concern]. That's actually pretty common. To give you the best advice, I need to understand your situation better:\n1. [Question 1]\n2. [Question 2]\n3. [Question 3]",
                    "expert": "[Reflect]. To narrow this down, I need:\n1. [Critical info]\n2. [Critical info]"
                }
            },
            
            ConversationState.DEEP_DIVING: {
                "max_words": 140 if user_mode == "guided" else 240,
                "must_end_with": "question or actionable_insight",
                "tone": "expert, detailed, confident",
                "structure": [
                    "show_understanding",
                    "provide_real_data_if_available",
                    "give_3_5_concrete_options",
                    "pros_cons_for_each",
                    "recommend_one_path",
                    "ask_follow_up"
                ],
                "include_data": True,
                "include_risks": True,
                "examples": {
                    "guided": "Alright, here's what's actually happening: [explanation in simple terms]\n\nYou have 3 paths:\n1. [Path] → [Outcome] ✓ Pros: [x,y,z] ✗ Cons: [a,b]\n2. [Path] → [Outcome] ✓ Pros [x,y,z] ✗ Cons: [a,b]\n3. [Path] → [Outcome] ✓ Pros: [x,y,z] ✗ Cons: [a,b]\n\nI'd recommend [Path] because [reason]. Does that make sense?",
                    "expert": "Current status: [Data]. Your options:\n1. [Path] - ROI: [x%]\n2. [Path] - ROI: [y%]\n3. [Path] - ROI: [z%]\nRecommend [path]. Questions?"
                }
            },
            
            ConversationState.ACTION_PLANNING: {
                "max_words": 200 if user_mode == "guided" else 300,
                "must_end_with": "action_or_commitment",
                "tone": "actionable, confident, planning-focused",
                "structure": [
                    "acknowledge_readiness",
                    "create_concrete_steps",
                    "include_deadlines",
                    "include_responsible_parties",
                    "include_success_metrics",
                    "ask_for_commitment"
                ],
                "format": "numbered_steps_only",
                "steps_count": 5 if user_mode == "guided" else 7,
                "examples": {
                    "guided": "Perfect! Here's your [timeframe] plan:\n\n📋 YOUR ACTION PLAN\n□ Step 1: [Action] | When: [Timeline] | Who: [You/Someone] | Success: [Metric]\n□ Step 2: [Action] | When: [Timeline] | Who: [You/Someone] | Success: [Metric]\n□ Step 3: [Action] | When: [Timeline] | Who: [You/Someone] | Success: [Metric]\n\n💪 Ready to do this? Should I set reminders for these?",
                    "expert": "Action plan:\n1. [Action] - [Date] - [Metric]\n2. [Action] - [Date] - [Metric]\n3. [Action] - [Date] - [Metric]\n\nCommit?"
                }
            },
            
            ConversationState.FOLLOWING_UP: {
                "max_words": 120 if user_mode == "guided" else 180,
                "must_end_with": "question_or_motivation",
                "tone": "encouraging, supportive, progress-focused",
                "structure": [
                    "acknowledge_progress",
                    "celebrate_wins",
                    "address_blockers",
                    "adjust_plan_if_needed",
                    "next_milestone"
                ],
                "examples": {
                    "guided": "Hey! 🎉 Great to see you back. Last we spoke, you were working on [previous action]. How's that going?\n\n✓ What's working?\n✗ What's blocking you?\n\nLet's adjust the plan based on what you've learned.",
                    "expert": "Progress check on [action]. Status?\n- Completed?\n- Blocked?\n- Need adjustment?\n\nNext steps:"
                }
            }
        }
        
        return rules.get(state, {})
    
    def detect_state_transition(self, previous_state: ConversationState, 
                               user_message: str, turn_count: int) -> ConversationState:
        """
        Smarter state detection based on actual user behavior patterns
        Focus on getting to actionable advice quickly
        """
        
        message_lower = user_message.lower()
        
        # Direct indicators for each state
        greeting_indicators = ["hi", "hello", "hey", "start", "begin", "help"]
        understanding_indicators = ["?", "help", "explain", "what", "how", "confused", "tell me", "want to know"]
        deep_dive_indicators = ["yes", "tell me more", "details", "explain more", "interested", "sure", "ok", "okay", "sounds good"]
        action_indicators = ["when", "how do i", "steps", "timeline", "let's do", "action", "plan", "start", "begin"]
        choice_indicators = ["resume bullets", "interview prep", "missing skills", "option", "choose", "select", "which one"]
        
        # Fast-track to action for experienced users
        if "expert" in message_lower or "direct" in message_lower or "just tell me" in message_lower:
            return ConversationState.ACTION_PLANNING
        
        # First interaction - always greeting
        if turn_count == 0 or previous_state == ConversationState.GREETING:
            return ConversationState.UNDERSTANDING
        
        # Force progression to avoid loops
        if turn_count > 2 and previous_state == ConversationState.UNDERSTANDING:
            return ConversationState.DEEP_DIVING
        
        if turn_count > 4 and previous_state == ConversationState.DEEP_DIVING:
            return ConversationState.ACTION_PLANNING
        
        # State transitions based on user intent
        if previous_state == ConversationState.UNDERSTANDING:
            if any(choice in message_lower for choice in choice_indicators):
                return ConversationState.DEEP_DIVING
            elif any(word in message_lower for word in deep_dive_indicators):
                return ConversationState.DEEP_DIVING
            elif any(word in message_lower for word in action_indicators):
                return ConversationState.ACTION_PLANNING
            else:
                return ConversationState.DEEP_DIVING  # Move forward by default
        
        elif previous_state == ConversationState.DEEP_DIVING:
            if any(choice in message_lower for choice in choice_indicators):
                return ConversationState.ACTION_PLANNING
            elif any(word in message_lower for word in action_indicators):
                return ConversationState.ACTION_PLANNING
            elif any(word in message_lower for word in deep_dive_indicators):
                return ConversationState.DEEP_DIVING
            else:
                return ConversationState.ACTION_PLANNING  # Push toward action
        
        elif previous_state == ConversationState.ACTION_PLANNING:
            if turn_count > 6:
                return ConversationState.FOLLOWING_UP
            elif any(word in message_lower for word in understanding_indicators):
                return ConversationState.UNDERSTANDING
            else:
                return ConversationState.ACTION_PLANNING
        
        elif previous_state == ConversationState.FOLLOWING_UP:
            if any(word in message_lower for word in action_indicators):
                return ConversationState.ACTION_PLANNING
            elif any(word in message_lower for word in deep_dive_indicators):
                return ConversationState.DEEP_DIVING
            else:
                return ConversationState.FOLLOWING_UP
        
        return previous_state
    
    def format_response(self, response_content: str, state: ConversationState,
                       domain: str = "") -> Tuple[str, Dict[str, Any]]:
        """
        Format response according to conversation state rules
        Returns: (formatted_response, metadata)
        """
        rules = self.get_response_rules(state, self.user_mode)
        max_words = rules.get("max_words", 200)
        tone = rules.get("tone", "neutral")
        
        # Word count enforcement
        words = response_content.split()
        if len(words) > max_words:
            # Truncate intelligently
            response_content = " ".join(words[:max_words]) + "..."

        # Ensure we end with a question when the state requires it.
        must_end = (rules.get("must_end_with") or "").lower()
        if "question" in must_end:
            trimmed = response_content.rstrip()
            if trimmed and not trimmed.endswith("?"):
                # If it ends with a period/ellipsis, convert to a question cue.
                response_content = trimmed.rstrip(".").rstrip("…").rstrip() + "?"
        
        # Add tone markers if guided mode
        if self.user_mode == "guided" and rules.get("emoji"):
            response_content = self._add_emoji_markers(response_content)
        
        # Ensure it ends with question if required
        if rules.get("must_end_with") == "question":
            if not response_content.rstrip().endswith("?"):
                response_content += "\n\nWhat would you like to explore next?"
        
        metadata = {
            "state": state.value,
            "word_count": len(response_content.split()),
            "tone": tone,
            "max_words": max_words,
            "mode": self.user_mode,
            "domain": domain
        }
        
        return response_content, metadata
    
    def _add_emoji_markers(self, text: str) -> str:
        """Add contextual emoji to make responses feel warmer"""
        
        emoji_map = {
            "success": "✓ ",
            "warning": "⚠️ ",
            "error": "❌ ",
            "money": "💰 ",
            "time": "⏰ ",
            "education": "📚 ",
            "career": "💼 ",
            "health": "🏥 ",
            "farm": "🌾 ",
            "legal": "⚖️ ",
            "step": "→ ",
            "tip": "💡 "
        }
        
        # Simple emoji injection based on keywords
        for keyword, emoji in emoji_map.items():
            if keyword.lower() in text.lower():
                # Inject emoji at start of lines containing keyword
                lines = text.split("\n")
                updated_lines = []
                for line in lines:
                    if keyword.lower() in line.lower() and not line.startswith(emoji):
                        updated_lines.append(emoji + line)
                    else:
                        updated_lines.append(line)
                text = "\n".join(updated_lines)
        
        return text
    
    def build_system_prompt(self, base_prompt: str, state: ConversationState,
                           user_memory: Dict[str, Any] = None) -> str:
        """
        Build system prompt with conversation rules injected
        This goes to the LLM to shape response behavior
        """
        rules = self.get_response_rules(state, self.user_mode)
        
        # Skip commitment templates for greetings
        if state == ConversationState.GREETING:
            rules["structure"] = ["warm_greeting", "ask_question"]
            rules["must_end_with"] = "question"
            rules["max_words"] = 20
        
        prompt = f"""
You are SwarmBharat - India's personal AI advisor.

CURRENT CONVERSATION STATE: {state.value.upper()}

=== RESPONSE RULES FOR THIS STATE ===
Tone: {rules.get('tone', 'neutral')}
Max words: {rules.get('max_words', 200)}
Structure: {', '.join(rules.get('structure', []))}
Must end with: {rules.get('must_end_with', 'answer')}

USER MODE: {self.user_mode.upper()}
{f'→ Hand-holding mode: Use simpler language, ask more questions' if self.user_mode == 'guided' else f'→ Expert mode: Direct answers, assume technical knowledge'}

=== CORE INSTRUCTIONS ===
1. Follow the structure specified for this conversation state
2. Respect word limits to keep responses focused
3. Use real data when available (don't make up statistics)
4. Reference user's known context (don't repeat questions they've answered)
5. Be specific - give exact steps, dates, amounts, phone numbers
6. For this state, prioritize: {rules.get('structure', ['answer'])[0] if rules.get('structure') else 'answer'}
7. NEVER add "Can you commit to this plan?" or "You're in charge, success will be measured by progress" to greetings

=== USER CONTEXT ===
{user_memory or 'No previous context'}

=== BASE PROMPT ===
{base_prompt}

Now respond following the rules above:
"""
        return prompt
    
    def add_message(self, user_id: str, role: str, content: str):
        """Add message to conversation history"""
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        self.sessions[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        return self.sessions.get(user_id, [])
    
    def next_turn(self, user_message: str) -> ConversationState:
        """Update state for next turn"""
        self.turn_count += 1
        self.current_state = self.detect_state_transition(
            self.current_state, 
            user_message,
            self.turn_count
        )
        return self.current_state
    
    def get_current_state_info(self) -> Dict[str, Any]:
        """Get info about current conversation state"""
        return {
            "state": self.current_state.value,
            "turn_count": self.turn_count,
            "user_mode": self.user_mode,
            "rules": self.get_response_rules(self.current_state, self.user_mode)
        }


# Example conversation flow
EXAMPLE_CONVERSATION = """
User uploads resume

[STATE: GREETING]
SwarmBharat: "Reviewed your resume — 4 years Python, currently at TCS Hyderabad. 
What's pushing you to make a change right now?"

User: "Salary is stuck at ₹8 LPA for 2 years"

[STATE: UNDERSTANDING]
SwarmBharat: "I understand — salary stagnation is frustrating. That's common after 3 years in service companies.
To help you effectively, I need to know:
1. Are you open to switching companies or promotion internally?
2. What kind of roles interest you?
3. What's your target salary?"

User: "Switch companies, maybe ML roles, looking for ₹15+ LPA"

[STATE: DEEP_DIVING]
SwarmBharat: "Good call — ML roles in Hyderabad are paying ₹15-22 LPA for your experience level right now.
Your Python is strong but you're missing 2 things recruiters filter on:
1. No public ML projects on GitHub (shows real work, not just theory)
2. No ML certification (AWS, Google, or Andrew Ng)

Both fixable in 2-3 months. Which would you like to tackle first?"

User: "Both actually. How do I do both?"

[STATE: ACTION_PLANNING]
SwarmBharat: "Perfect! Here's your 90-day plan:

MONTH 1: Build ML Project
□ Week 1-2: Pick dataset (Kaggle) + define problem
□ Week 3-4: Code + document on GitHub
✓ Success: Project live on GitHub with 1000+ lines of Python

MONTH 2: AWS ML Certification
□ Week 5-6: Study AWS ML Specialty course
□ Week 7-8: Practice exams, 80%+ score
✓ Success: AWS ML Specialty certified

MONTH 3: Apply to Jobs
□ Week 9-10: Polish resume, apply to 20+ companies
□ Week 11-12: Interview prep, negotiate offers
✓ Success: Job offer ₹15+ LPA

Ready to start? Should I send reminders each week?"

User: "Yes, start Monday"

[STATE: FOLLOWING_UP - next week]
SwarmBharat: "Hey Ravi! 🚀 Week 1 is here!

How's the ML project coming?
✓ Found dataset?
✗ Stuck somewhere?

Remember: Just start. Perfect is the enemy of done. Let me know blockers."
"""
