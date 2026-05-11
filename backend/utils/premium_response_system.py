"""
Premium Response System - Claude-like Experience at 10% Cost
Hybrid approach: Templates for 80% users, Claude API for 20% premium users
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from dataclasses import dataclass
import logging

# AI Models - Use available models
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Ollama for local models
try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ResponseMetadata:
    user_tier: str
    response_type: str  # "template", "claude", "groq"
    cost: float
    confidence: float
    processing_time: float

class PremiumResponseSystem:
    """
    Hybrid response system that delivers Claude-like quality at sustainable costs
    """
    
    def __init__(self):
        # AI Model Clients - Initialize only available models
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) if CLAUDE_AVAILABLE else None
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY")) if GROQ_AVAILABLE else None
        self.openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if OPENAI_AVAILABLE else None
        
        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        
        # Cost tracking
        self.cost_per_token = {
            "claude": 0.015,  # $15 per 1M tokens
            "groq": 0.00005,  # $0.05 per 1M tokens
            "openai": 0.002,  # $2 per 1M tokens
            "ollama": 0.0     # Free local model
        }
        
        # Response templates for free tier
        self.templates = self._load_response_templates()
        
        # Performance tracking
        self.response_stats = {
            "total_responses": 0,
            "template_responses": 0,
            "claude_responses": 0,
            "total_cost": 0.0
        }
    
    async def generate_response(
        self, 
        query: str, 
        domain: str, 
        user_data: Dict[str, Any],
        api_data: Optional[Dict[str, Any]] = None,
        user_tier: str = "free"
    ) -> Dict[str, Any]:
        """
        Generate premium response based on user tier and context
        
        Returns:
        {
            "response": "Beautiful conversational response",
            "metadata": ResponseMetadata,
            "actions": ["suggested actions"],
            "confidence": 0.95
        }
        """
        start_time = datetime.now()
        
        # Route to appropriate response generator based on available models
        if user_tier == "premium" and self.claude and self._should_use_claude(query, domain):
            response_data = await self._generate_claude_response(query, domain, user_data, api_data)
            response_type = "claude"
        elif user_tier in ["pro", "business"] and self.groq:
            response_data = await self._generate_groq_response(query, domain, user_data, api_data)
            response_type = "groq"
        elif OLLAMA_AVAILABLE:
            # Use Ollama for free tier - no cost!
            response_data = await self._generate_ollama_response(query, domain, user_data, api_data)
            response_type = "ollama"
        else:
            response_data = await self._generate_template_response(query, domain, user_data, api_data)
            response_type = "template"
        
        # Calculate processing time and cost
        processing_time = (datetime.now() - start_time).total_seconds()
        cost = self._calculate_cost(response_type, response_data.get("tokens_used", 0))
        
        # Update stats
        self.response_stats["total_responses"] += 1
        self.response_stats[f"{response_type}_responses"] += 1
        self.response_stats["total_cost"] += cost
        
        # Create metadata
        metadata = ResponseMetadata(
            user_tier=user_tier,
            response_type=response_type,
            cost=cost,
            confidence=response_data.get("confidence", 0.8),
            processing_time=processing_time
        )
        
        return {
            "response": response_data["text"],
            "metadata": metadata,
            "actions": response_data.get("actions", []),
            "confidence": response_data.get("confidence", 0.8),
            "sources": response_data.get("sources", []),
            "data_blocks": response_data.get("data_blocks", [])
        }
    
    async def _generate_claude_response(
        self, 
        query: str, 
        domain: str, 
        user_data: Dict[str, Any], 
        api_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Claude response for premium users"""
        
        system_prompt = self._get_claude_system_prompt(domain)
        
        user_message = f"""
        User Query: {query}
        Domain: {domain}
        User Profile: {json.dumps(user_data, indent=2)}
        API Data: {json.dumps(api_data or {}, indent=2)}
        
        Generate a beautiful, conversational response that:
        1. Addresses the user's specific situation
        2. Incorporates real-time data naturally
        3. Uses emojis and friendly tone
        4. Provides actionable next steps
        5. Shows confidence in recommendations
        6. Includes relevant data visualizations
        
        Format your response as JSON:
        {{
            "text": "Your conversational response",
            "confidence": 0.95,
            "actions": ["action1", "action2"],
            "sources": ["source1", "source2"],
            "data_blocks": [
                {{
                    "type": "job_match",
                    "title": "Top Matches",
                    "data": [...]
                }}
            ]
        }}
        """
        
        try:
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            
            # Parse JSON response
            response_text = response.content[0].text
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "text": response_text,
                    "confidence": 0.9,
                    "actions": [],
                    "sources": ["Claude AI"],
                    "data_blocks": []
                }
                
        except Exception as e:
            logger.error(f"Claude response failed: {str(e)}")
            return await self._generate_fallback_response(query, domain, user_data, api_data)
    
    async def _generate_groq_response(
        self, 
        query: str, 
        domain: str, 
        user_data: Dict[str, Any], 
        api_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Groq response for pro users"""
        
        system_prompt = f"""
        You are SwarmBharat AI's friendly {domain} advisor.
        Generate conversational responses that are:
        - Warm and encouraging
        - Data-driven but simple
        - Action-oriented
        - Include relevant emojis
        - Under 300 words
        """
        
        user_message = f"""
        Query: {query}
        User: {json.dumps(user_data)}
        Data: {json.dumps(api_data or {})}
        
        Provide a helpful response with suggested actions.
        """
        
        try:
            response = self.groq.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            return {
                "text": response_text,
                "confidence": 0.85,
                "actions": self._extract_actions(response_text),
                "sources": ["Groq Llama3"],
                "data_blocks": self._create_data_blocks(api_data, domain)
            }
            
        except Exception as e:
            logger.error(f"Groq response failed: {str(e)}")
            return await self._generate_fallback_response(query, domain, user_data, api_data)
    
    async def _generate_template_response(
        self, 
        query: str, 
        domain: str, 
        user_data: Dict[str, Any], 
        api_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate template-based response for free users"""
        
        template = self.templates.get(domain, self.templates["default"])
        
        # Personalize template with user data
        personalized_response = template.format(
            user_name=user_data.get("name", "Friend"),
            location=user_data.get("location", "your city"),
            query=query,
            **(api_data or {})
        )
        
        return {
            "text": personalized_response,
            "confidence": 0.75,
            "actions": self._get_domain_actions(domain),
            "sources": ["SwarmBharat Knowledge Base"],
            "data_blocks": self._create_data_blocks(api_data, domain)
        }
    
    async def _generate_ollama_response(
        self, 
        query: str, 
        domain: str, 
        user_data: Dict[str, Any], 
        api_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate response using Ollama local model - FREE!"""
        
        system_prompt = self._get_claude_system_prompt(domain)
        
        user_message = f"""
        User Query: {query}
        Domain: {domain}
        User Profile: {json.dumps(user_data, indent=2)}
        API Data: {json.dumps(api_data or {}, indent=2)}
        
        Generate a beautiful, conversational response that:
        1. Addresses the user's specific situation
        2. Incorporates real-time data naturally
        3. Uses emojis and friendly tone
        4. Provides actionable next steps
        5. Shows confidence in recommendations
        
        Keep it conversational like Claude, under 300 words.
        """
        
        try:
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "system": system_prompt,
                    "prompt": user_message,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                return {
                    "text": response_text,
                    "confidence": 0.85,
                    "actions": self._extract_actions(response_text),
                    "sources": [f"Ollama ({self.ollama_model})"],
                    "data_blocks": self._create_data_blocks(api_data, domain),
                    "tokens_used": len(response_text.split())
                }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return await self._generate_fallback_response(query, domain, user_data, api_data)
                
        except Exception as e:
            logger.error(f"Ollama response failed: {str(e)}")
            return await self._generate_fallback_response(query, domain, user_data, api_data)
    
    async def _generate_fallback_response(
        self, 
        query: str, 
        domain: str, 
        user_data: Dict[str, Any], 
        api_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback response when AI models fail"""
        
        fallback_text = f"""
        I'm here to help with your {domain} query! 
        
        Based on what you've shared about {query}, I'd recommend:
        • Taking time to research your options
        • Consulting with a professional if needed
        • Checking official government resources
        
        I'm constantly learning to provide better responses. 
        Would you like me to connect you with more detailed resources?
        """
        
        return {
            "text": fallback_text,
            "confidence": 0.5,
            "actions": ["Get more information", "Talk to expert"],
            "sources": ["Fallback Response"],
            "data_blocks": []
        }
    
    def _get_claude_system_prompt(self, domain: str) -> str:
        """Get domain-specific Claude system prompt"""
        
        prompts = {
            "career": """
            You are SwarmBharat's expert career advisor. You're encouraging, data-driven, and practical.
            Transform job data into actionable career advice. Always include:
            - Salary expectations and market rates
            - Skill gaps and learning recommendations
            - Company insights and culture tips
            - Next steps for applications
            Use emojis and conversational tone like texting a knowledgeable friend.
            """,
            
            "finance": """
            You are SwarmBharat's friendly financial advisor. You make finance simple and accessible.
            Transform market data into actionable investment advice. Always include:
            - Risk assessment and disclaimers
            - Market context and trends
            - Practical next steps
            - Educational explanations
            Use relevant emojis (📈📉💰) and keep it under 250 words.
            """,
            
            "farming": """
            You are SwarmBharat's farming expert. You understand Indian agriculture deeply.
            Transform weather and commodity data into practical farming advice. Always include:
            - Weather-related actions
            - Market timing recommendations
            - Government scheme information
            - Regional farming insights
            Use simple language and farming metaphors.
            """,
            
            "immigration": """
            You are SwarmBharat's immigration specialist. You simplify complex visa processes.
            Transform immigration rules into actionable guidance. Always include:
            - Clear step-by-step processes
            - Document requirements
            - Timeline expectations
            - Common pitfalls to avoid
            Be encouraging but realistic about processing times.
            """
        }
        
        return prompts.get(domain, prompts["career"])
    
    def _should_use_claude(self, query: str, domain: str) -> bool:
        """Determine if query warrants Claude API usage"""
        
        # Use Claude for complex queries
        claude_triggers = [
            "analyze", "compare", "recommend", "strategy", "plan",
            "investment", "career change", "immigration", "legal"
        ]
        
        query_lower = query.lower()
        return any(trigger in query_lower for trigger in claude_triggers)
    
    def _extract_actions(self, response_text: str) -> List[str]:
        """Extract actionable items from response"""
        action_keywords = ["apply", "contact", "check", "download", "register", "visit"]
        actions = []
        
        for keyword in action_keywords:
            if keyword in response_text.lower():
                actions.append(f"Get {keyword} help")
        
        return actions[:3]  # Limit to 3 actions
    
    def _get_domain_actions(self, domain: str) -> List[str]:
        """Get default actions for domain"""
        
        domain_actions = {
            "career": ["Update resume", "Practice interview", "Skill assessment"],
            "finance": ["Investment calculator", "Risk assessment", "Portfolio review"],
            "farming": ["Weather alert", "Market prices", "Scheme eligibility"],
            "immigration": ["Document checklist", "Eligibility test", "Timeline calculator"],
            "health": ["Find hospital", "Insurance comparison", "Health checkup"],
            "legal": ["Rights guide", "Document template", "Lawyer consultation"],
            "business": ["GST registration", "Loan eligibility", "Compliance check"],
            "education": ["Scholarship search", "College finder", "Loan calculator"],
            "government": ["Scheme finder", "Application tracker", "Eligibility test"]
        }
        
        return domain_actions.get(domain, ["Get more info", "Talk to expert"])
    
    def _create_data_blocks(self, api_data: Optional[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
        """Create data visualization blocks"""
        
        if not api_data:
            return []
        
        blocks = []
        
        if domain == "career" and "jobs" in api_data:
            blocks.append({
                "type": "job_matches",
                "title": "🎯 Top Job Matches",
                "data": api_data["jobs"][:3]
            })
        
        elif domain == "finance" and "prices" in api_data:
            blocks.append({
                "type": "market_data",
                "title": "📊 Market Data",
                "data": api_data["prices"]
            })
        
        elif domain == "farming" and "commodities" in api_data:
            blocks.append({
                "type": "commodity_prices",
                "title": "🌾 Commodity Prices",
                "data": api_data["commodities"]
            })
        
        return blocks
    
    def _calculate_cost(self, response_type: str, tokens_used: int) -> float:
        """Calculate response cost"""
        cost_per_token = self.cost_per_token.get(response_type, 0.001)
        return (tokens_used * cost_per_token) / 1000  # Convert to dollars
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load Claude-like response templates for free tier"""
        
        return {
            "career": """
            🎯 Great question, {user_name}! I'm excited to help you with your career journey in {location}!
            
            Looking at your query about "{query}", I can see you're being proactive about your professional growth - that's fantastic! 🌟
            
            Here's what I'm seeing in the current market:
            • **Skills in demand**: The tech scene in {location} is really heating up, especially for roles that combine technical expertise with business acumen
            • **Salary trends**: Companies are offering competitive packages, but the real value is in the growth opportunities
            • **Application strategy**: Quality over quantity - tailor each application to show how your unique story aligns with their mission
            
            The job market is dynamic, but your approach of seeking guidance puts you ahead of the curve! 💪
            
            What specific aspect would you like to dive deeper into - resume optimization, interview prep, or identifying the right companies for your values?
            """,
            
            "finance": """
            💰 Smart thinking, {user_name}! Financial planning is one of the most powerful tools for building the life you want.
            
            Your question about "{query}" shows you're taking control of your financial future - that's the first and most important step! 🚀
            
            Here's my take on building lasting wealth:
            • **Start with your 'why'**: Are you building for security, freedom, or legacy? Your goals shape your strategy
            • **The magic of consistency**: Small, regular investments often outperform timing the market
            • **Diversity is your best friend**: Don't put all your eggs in one basket - spread across different asset classes
            • **Stay curious**: The financial world evolves quickly, but solid principles never go out of style
            
            Remember: You don't need to be an expert to start, but you need to start to become an expert! 📈
            
            Would you like to explore specific investment vehicles or create a personalized financial roadmap?
            """,
            
            "farming": """
            🌾 Namaste, {user_name}! Your dedication to farming and sustainable agriculture truly inspires me! 🙏
            
            Regarding "{query}", I can tell you're not just growing crops - you're nurturing the future of our communities. That's incredible work!
            
            Here's what I'm seeing in the agricultural landscape:
            • **Weather patterns**: The changing climate requires adaptive farming strategies - but your traditional knowledge combined with modern tech is a winning combination
            • **Market opportunities**: Consumers are increasingly valuing organic, locally-grown produce - your timing is perfect!
            • **Government support**: There are some fantastic schemes designed specifically for farmers like you who are committed to sustainable practices
            
            Your connection to the land is something special, and leveraging both traditional wisdom and modern innovations will help your farm thrive for generations to come. 🌱
            
            What specific challenges or opportunities are you most excited about right now?
            """,
            
            "immigration": """
            � {user_name}, your ambition to explore global opportunities is truly admirable! The world needs more people with your courage and vision. ✨
            
            About "{query}" - this is one of the most significant decisions you'll make, and your thoughtful approach shows you're ready for this journey.
            
            Here's what I want you to know:
            • **Your story matters**: Immigration isn't just about paperwork - it's about sharing your unique gifts with a new community
            • **Preparation is everything**: The more organized you are with documentation, the smoother your journey will be
            • **Cultural bridge**: You're not just moving countries - you're building bridges between communities
            • **Timing**: Processing times vary, but your patience and persistence will pay off
            
            This path requires resilience, but from what I can see, you have exactly what it takes to succeed! 💪
            
            Which aspect of the immigration process feels most overwhelming right now? Let's break it down together.
            """,
            
            "default": """
            🌟 {user_name}, I'm genuinely excited to help you with "{query}"! Your curiosity and desire to make informed decisions really sets you apart. 🎯
            
            Here's what I'm thinking:
            • **Your approach**: Taking time to research and ask questions shows wisdom - you're building a foundation for success
            • **Multiple perspectives**: Every situation has different angles, and exploring them all helps you make the best choice
            • **Action-oriented thinking**: You're not just gathering information - you're planning your next steps
            
            Remember: The most successful people aren't those who have all the answers, but those who keep asking the right questions. And you're definitely asking the right questions! 🚀
            
            What specific aspect would you like to explore first? I'm here to help you navigate this decision with confidence.
            """
        }
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        
        total_responses = self.response_stats["total_responses"]
        if total_responses == 0:
            return {"error": "No responses generated yet"}
        
        return {
            "total_responses": total_responses,
            "template_ratio": self.response_stats["template_responses"] / total_responses,
            "claude_ratio": self.response_stats["claude_responses"] / total_responses,
            "total_cost": self.response_stats["total_cost"],
            "cost_per_response": self.response_stats["total_cost"] / total_responses,
            "estimated_monthly_cost": self.response_stats["total_cost"] * 30  # Rough estimate
        }
