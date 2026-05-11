"""
SwarmBharat AI - Dynamic Response Generator
Generates domain-aware, consultant-style responses using LLMs with
emotion detection, urgency awareness, and multi-agent debate integration.
Supports all file types and all Indian domains.
"""

import os
import httpx
import logging
from typing import Dict, Any
from langdetect import detect

logger = logging.getLogger(__name__)

# Sarvam API configuration
SARVAM_KEY = os.getenv("SARVAM_API_KEY")

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang  # 'hi' for Hindi, 'te' for Telugu, 'en' for English
    except:
        return 'en'

async def translate_with_sarvam(text: str, target_lang: str) -> str:
    if not SARVAM_KEY or target_lang == 'en':
        return text
    
    lang_map = {
        'hi': 'hi-IN',
        'te': 'te-IN',
        'ta': 'ta-IN',
        'kn': 'kn-IN',
        'mr': 'mr-IN'
    }
    
    target = lang_map.get(target_lang)
    if not target:
        return text
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sarvam.ai/translate",
                headers={
                    "api-subscription-key": SARVAM_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "source_language_code": "en-IN",
                    "target_language_code": target,
                    "speaker_gender": "Female",
                    "mode": "formal",
                    "enable_preprocessing": True
                },
                timeout=10.0
            )
            data = response.json()
            return data.get("translated_text", text)
    except Exception as e:
        print(f"Sarvam translation error: {e}")
        return text

class DynamicResponseGenerator:
    """
    Generates dynamic, consultant-style responses using LLMs,
    taking into account emotion, urgency, and user context.
    """
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    async def _call_groq(self, system: str, user: str, max_tokens: int = 2000) -> str:
        import asyncio as _asyncio

        if not self.groq_api_key:
            return await self._call_ollama(system, user)

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        
        user_trimmed = (user[:12000] + "\n[truncated]") if len(user) > 12000 else user
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_trimmed},
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }

        # Retry with exponential backoff for rate limits
        for attempt in range(3):
            async with httpx.AsyncClient(timeout=90.0) as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload, headers=headers
                )
                if r.status_code == 429:
                    wait = 2 ** attempt + 1
                    logger.warning(f"Groq 429 rate limit, retrying in {wait}s (attempt {attempt+1}/3)")
                    await asyncio.sleep(wait)
                    continue
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()

        # All retries exhausted — fall back to Ollama
        logger.warning("Groq rate limit persistent, falling back to Ollama")
        return await self._call_ollama(system, user)

    async def _call_ollama(self, system: str, user: str, max_tokens: int = 2000) -> str:
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": max_tokens,
            }
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(f"{self.ollama_url}/api/chat", json=payload)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()

    async def generate_response(
        self,
        query: str,
        domain: str = "general",
        emotion: str = "neutral",
        urgency: str = "medium",
        user_data: Dict[str, Any] = None,
        user_choices: Dict[str, Any] = None,
        conversation_context: Dict[str, Any] = None,
        document_text: str = "",
        debate_result: Dict[str, Any] = None,
        real_data: Dict[str, Any] = None,
        system_prompt: str = None,
        max_tokens: int = 1500,
        document: dict = None
    ) -> str:
        """
        Generate contextual, domain-aware consultant response using the LLM.
        Now integrates real-time data and actual debate insights.
        """
        
        # Check for greeting first
        greetings = [
            'hello', 'hi', 'hey', 'namaste', 'hii', 'helo', 'helloo',
            'good morning', 'good evening', 'good afternoon', 'good night',
            'sup', 'wassup', 'hola', 'vanakkam', 'namaskar', 'kem cho',
            'sat sri akal', 'jai hind', 'howdy', 'greetings'
        ]
        
        msg_clean = query.lower().strip().rstrip('!.,?')
        if (msg_clean in greetings or 
            any(msg_clean.startswith(g) for g in greetings) or
            len(msg_clean.split()) <= 2 and any(g in msg_clean for g in greetings)):
            return "Namaste! Great to have you here.\nWhat would you like help with today?"
        user_data = user_data or {}
        user_choices = user_choices or {}
        conversation_context = conversation_context or {}
        real_data = real_data or {}
        
        city = user_data.get('personal', {}).get('city') or user_data.get('city', 'Hyderabad')
        debate_summary = debate_result.get('final_synthesis', '') if debate_result else ''
        
        # Build domain-specific expert persona with REAL Indian context
        domain_personas = {
            "career": f"You are a senior career coach with 20+ years in the Indian job market. You have placed 500+ candidates in Hyderabad, Bangalore, and Pune. You know exactly what TCS, Infosys, and startups are paying in 2025. Current city: {city}.",
            "health": f"You are a medical report analyst and health advisor familiar with Indian healthcare systems, Aarogyasri (Telangana), Ayushman Bharat, and local hospital networks in {city}. Always recommend consulting licensed doctors.",
            "finance": f"You are a SEBI-registered investment advisor specializing in Indian markets, NSE/BSE, mutual funds (SIPs), tax planning (Section 80C), and real estate in {city}. You track Nifty50, Sensex, and RBI policy changes daily.",
            "immigration": "You are a certified immigration consultant specializing in Canada Express Entry, Australia PR, and UK visas for Indian applicants. You track CRS score changes, draw dates, and processing times exactly as they happen.",
            "farming": f"You are an agricultural expert for Telangana/Andhra Pradesh with deep knowledge of PM-Kisan, Rythu Bandhu, crop insurance, and market rates at {city} market. You understand monsoon patterns and MSP changes.",
            "government": "You are an expert in Indian government schemes with real-time knowledge of application deadlines, eligibility criteria, and MeeSeva/DigiLocker processes. You know which schemes are currently accepting applications.",
            "legal": "You are a legal information expert for India with knowledge of IPC/CrPC sections, DLSA free legal aid, and local court procedures in Hyderabad. You provide actionable legal guidance.",
            "business": f"You are a startup mentor who has helped 50+ Indian businesses get MSME loans, Startup India recognition, and GST registration. You understand the {city} business ecosystem and current market opportunities.",
            "education": "You are an education counselor covering JEE/NEET/GATE/UPSC with current cutoffs, exam dates, and counseling procedures. You track NIT/IIT placements and scholarship deadlines.",
            "mental_health": "You are an empathetic mental wellness counselor familiar with Indian cultural context, family dynamics, and stigma around mental health. You provide practical, evidence-based guidance.",
            "real_estate": f"You are a real estate advisor specializing in {city} property market, RERA compliance, stamp duty calculations, and home loan options from SBI/HDFC/ICICI banks.",
        }
        persona = domain_personas.get(domain, "You are SwarmBharat AI, an expert multi-domain consultant for Indian users.")

        # Build REAL data injection section
        real_data_section = ""
        if real_data:
            real_data_section = "\n\n=== LIVE DATA FETCHED JUST NOW ===\n"
            for source, data in real_data.items():
                if isinstance(data, dict) and data.get('status') != 'error':
                    if source == 'jobs' and data.get('jobs'):
                        real_data_section += f"\n📈 LIVE JOBS: Found {len(data['jobs'])} positions in {city}\n"
                        for job in data['jobs'][:3]:
                            real_data_section += f"  • {job.get('title', 'N/A')} at {job.get('company', 'N/A')} - {job.get('salary', 'Salary not disclosed')}\n"
                    elif source == 'salary' and data.get('data'):
                        real_data_section += f"\n💰 SALARY DATA: {data['data'].get('min', 'N/A')} - {data['data'].get('max', 'N/A')} {data['data'].get('currency', 'INR')}\n"
                    elif source == 'weather':
                        real_data_section += f"\n🌤️ WEATHER: {data.get('temperature', 'N/A')}°C, {data.get('weather', 'N/A')}\n"
                    elif source == 'express_entry':
                        real_data_section += f"\n🇨🇦 EXPRESS ENTRY: Latest draw cutoff {data.get('crs_score_needed', 'Check latest')}\n"
                    elif source == 'gold':
                        real_data_section += f"\n🥇 GOLD PRICE: ₹{data.get('price_per_gram', 'N/A')}/gram\n"
            real_data_section += "\n=== USE THIS LIVE DATA IN YOUR RESPONSE ===\n"
        
        # Use custom system prompt if provided, otherwise build default
        if system_prompt:
            final_system_prompt = system_prompt
        else:
            final_system_prompt = f"""{persona}

{real_data_section}

User Profile:
- Location: {city}
- Domain: {domain}
- Emotional State: {emotion}
- Urgency: {urgency}
- Previous Choices: {list(user_choices.keys()) if user_choices else 'None'}

Agent Debate Insights:
{debate_summary[:800] if debate_summary else 'Direct expert consultation'}

You are SwarmBharat AI — a warm, conversational Indian life assistant.
You text like a knowledgeable friend, not a consultant or robot.

YOUR PERSONALITY:
- Use contractions (you're, don't, it's, can't, won't, I'd)
- Short sentences only (max 2 lines per thought)
- Use "I" and "we" (never "the system")
- Sound like texting a friend (casual, warm, encouraging)
- 1-2 emojis per paragraph (not more, not less)
- Ask more questions than statements
- Validate emotions BEFORE giving advice
- Admit uncertainty when needed ("I'm not 100% sure, but...")
- Be encouraging but honest
- Use natural filler ("So here's the thing...", "Listen...", "Real talk...")

YOUR 7-PART RESPONSE STRUCTURE:

[PART 1 - ACKNOWLEDGEMENT]: Start with emotion + emoji
  - Acknowledge user's feeling (awesome/tough/scary/confusing)
  - Use relevant emoji
  - Example: "That's awesome! 🎉" or "That sucks! 😞"

[PART 2 - VALIDATION]: Validate their concern
  - Show you understand why they're asking
  - Make them feel heard
  - Example: "You're thinking about the right thing"

[PART 3 - CONTEXT/EXPLANATION]: Explain why this matters
  - Give background in simple language
  - Use real Indian data point (₹ amount, scheme name, deadline)
  - Example: "Here's why this matters: Prices jump 2.5% = unusual..."

[PART 4 - SPECIFIC ACTION]: Give concrete steps
  - 2-4 specific steps with timeline (this week, today, next month)
  - Be specific (not "consider investing", say "invest ₹60K")
  - Example: "So here's what I'd do: Apply to 5 companies THIS WEEK"

[PART 5 - CLARIFYING QUESTION]: Ask to personalize
  - Use "Quick question:" prefix
  - Ask for missing context
  - Example: "Quick question: Do you have an emergency fund?"

[PART 6 - NEXT STEP/HOMEWORK]: Give clear action
  - When should they do it
  - What exactly should they do
  - Example: "This week: Check emergency fund. Next week: open mutual fund"

[PART 7 - CLOSING ENGAGEMENT]: End with question
  - Keep dialogue open
  - Related to their situation
  - Add relevant emoji
  - Example: "How much have you saved for emergencies? 💰"

DOMAIN-SPECIFIC TONE:

CAREER: Motivating, encouraging 💪📈🎯
- Celebrate small wins
- Acknowledge job search is stressful

FINANCE: Honest, cautious but optimistic 📈💰⚠️
- Always explain risks
- Admit market uncertainty
- Give context before advice

FARMING: Practical, respectful 🌾💚📊
- Use simple language
- Explain agricultural terms
- Give seasonal context

IMMIGRATION: Empathetic, reassuring 🛫🎓🌍
- Acknowledge complexity
- Give clear timelines
- Explain processes simply

HEALTH: Empathetic, simplifying 💙🏥💊
- Acknowledge anxiety
- Simplify medical jargon
- Explain why choices matter

LEGAL: Confident, protective ⚖️💪📋
- Give confidence (user feels powerless)
- Explain laws simply
- Always add "consult lawyer for final decision"

BUSINESS: Practical, simplified 💼📊✅
- Simplify complexity
- Give specific numbers
- Remove fear factor

EDUCATION: Excited, supportive 🎓✅📚
- Show excitement
- Simplify processes
- Give specific amounts/timelines

GOVERNMENT: Informative, empowering 🏛️💰✅
- Empower users with info
- Give specific scheme names
- Make it feel achievable

STRICT RULES:
1. NEVER sound formal or robotic ("Pursuant to your inquiry...")
2. NEVER give generic advice everyone knows
3. NEVER ignore user's emotional state
4. NEVER end with period (always question)
5. NEVER use more than 2 emojis per paragraph
6. NEVER pretend to be human (can say "I'm an AI but...")
7. NEVER give financial/legal/medical advice (say "I can't give advice, but here's context...")
8. ALWAYS include one real Indian data point
9. ALWAYS complete sentences
10. Max 200 words
11. For greetings ONLY: "Namaste! Great to have you here. What would you like help with today?"
12. For documents — reference SPECIFIC content from document
"""

        # Build user content for API call
        if document:
            # Handle base64 document from frontend
            user_content = [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": document.get("media_type", "application/pdf"),
                        "data": document.get("data", "")
                    }
                },
                {
                    "type": "text",
                    "text": f"User Query: {query}\n\nPlease read the uploaded PDF and respond based on its actual content."
                }
            ]
            # For now, convert to text format for Groq/Ollama
            user_prompt = f"User Query: {query}\n\nUPLOADED DOCUMENT: {document.get('filename', 'unknown_file')} (base64 data provided)\n\nPlease read the uploaded PDF and respond based on its actual content."
        else:
            user_prompt = f"User Query: {query}\n"
            if document_text:
                user_prompt += f"\nUploaded Document Text:\n{document_text[:3000]}\n"

        # Add debate results to the system prompt if available
        if debate_result and isinstance(debate_result, dict):
            debate_text = ""
            if 'researcher' in debate_result:
                debate_text += f"\nRESEARCHER FOUND: {debate_result['researcher']}"
            if 'accountant' in debate_result:
                debate_text += f"\nFINANCIAL ANALYSIS: {debate_result['accountant']}"
            if 'risk' in debate_result:
                debate_text += f"\nRISKS TO KNOW: {debate_result['risk']}"
            if 'mentor' in debate_result:
                debate_text += f"\nRECOMMENDED STEPS: {debate_result['mentor']}"
            
            if debate_text:
                # Update the system prompt to include debate synthesis with conversational style
                synthesis_prompt = f"""
You are SwarmBharat AI — texting like a knowledgeable friend.

Based on research from 4 specialist agents, give ONE conversational answer.

{debate_text}

USER ASKED: {user_prompt}

USE THIS 7-PART STRUCTURE:

[PART 1] Acknowledge emotion + emoji ("That's awesome! 🎉" or "That sucks! 😔")

[PART 2] Validate their concern ("You're thinking about the right thing")

[PART 3] Explain context with real data (₹ amount, scheme name, deadline)

[PART 4] Give 2-4 specific actions with timeline (this week/today/next month)

[PART 5] Ask clarifying question ("Quick question: Do you have...?")

[PART 6] Give homework ("This week: Check... Next week: Apply...")

[PART 7] End with engagement question + emoji

RULES:
- Use contractions (you're, don't, it's)
- Short sentences (max 2 lines)
- 1-2 emojis per paragraph
- Sound like texting a friend
- End with question (not period)
- Max 200 words
- Include one real Indian data point
- NEVER say "I don't see a document" if document text was provided
"""
                user_prompt = synthesis_prompt

        try:
            # Use custom max_tokens to prevent cutoff
            response = await self._call_groq(final_system_prompt, user_prompt, max_tokens=max_tokens)
            
            # Detect user language and translate if needed
            user_language = detect_language(query)
            if user_language in ['hi', 'te', 'ta', 'kn', 'mr']:
                response = await translate_with_sarvam(response, user_language)
            
            return response
        except Exception as e:
            logger.warning(f"Groq failed, falling back to Ollama: {e}")
            try:
                response = await self._call_ollama(final_system_prompt, user_prompt, max_tokens=max_tokens)
                
                # Detect user language and translate if needed
                user_language = detect_language(query)
                if user_language in ['hi', 'te', 'ta', 'kn', 'mr']:
                    response = await translate_with_sarvam(response, user_language)
                
                return response
            except Exception as e2:
                logger.error(f"Both LLMs failed: {e2}")
                return "I apologize, but I am unable to process your request at the moment due to a service interruption. Please try again later."
