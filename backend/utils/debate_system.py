"""
Real-time AI Debate System for SwarmBharat AI
Shows agents thinking and debating in real-time, not just final answers
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Dict, Any, List, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor, as_completed, FIRST_COMPLETED
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentResponse:
    agent_name: str
    confidence: float
    reasoning: str
    sources: List[str]
    processing_time: float

@dataclass
class DebateSynthesis:
    final_answer: str
    overall_confidence: float
    agent_agreements: Dict[str, bool]
    key_insights: List[str]
    reasoning_summary: str

class DebateAgent:
    """Individual AI agent with specific domain expertise"""
    
    def __init__(self, name: str, expertise: str, personality: str):
        self.name = name
        self.expertise = expertise
        self.personality = personality
        self.processing_delay = self._get_processing_delay()
    
    def _get_processing_delay(self) -> float:
        """Simulate realistic thinking time"""
        if self.expertise == "finance":
            return 1.5  # Finance needs more calculation
        elif self.expertise == "legal":
            return 2.0  # Legal needs careful consideration
        elif self.expertise == "risk":
            return 1.2  # Risk assessment is faster
        else:
            return 1.0
    
    async def think(self, query: str, domain: str, user_context: Dict[str, Any] = None) -> AgentResponse:
        """Process query and return agent's perspective"""
        start_time = datetime.now()
        
        # Simulate thinking time
        await asyncio.sleep(self.processing_delay)
        
        # Generate response based on agent expertise
        reasoning = await self._generate_reasoning(query, domain, user_context)
        confidence = await self._calculate_confidence(query, domain)
        sources = await self._identify_sources(query, domain)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResponse(
            agent_name=self.name,
            confidence=confidence,
            reasoning=reasoning,
            sources=sources,
            processing_time=processing_time
        )
    
    async def _generate_reasoning(self, query: str, domain: str, user_context: Dict[str, Any]) -> str:
        """Generate agent-specific reasoning"""
        
        reasoning_templates = {
            "finance": {
                "investment": f"From a financial perspective, {query} involves considering risk tolerance, time horizon, and diversification. Based on market data and historical returns, ",
                "career": f"Financially speaking, {query} impacts earning potential and career growth. Key factors include salary trajectory, skills demand, and ",
                "business": f"The financial implications of {query} include cash flow, ROI, and risk management. Important considerations are "
            },
            "legal": {
                "investment": f"Legally, {query} requires understanding tax implications, regulatory compliance, and documentation requirements. Key legal aspects include ",
                "career": f"From an employment law perspective, {query} involves contract terms, labor laws, and employee rights. Critical legal points are ",
                "business": f"Legally, {query} requires compliance with business regulations, intellectual property, and liability. Essential legal considerations include "
            },
            "risk": {
                "investment": f"Risk assessment for {query} involves market volatility, liquidity risk, and concentration risk. Key risk factors include ",
                "career": f"Career risks for {query} include market demand, skill obsolescence, and economic factors. Risk mitigation strategies involve ",
                "business": f"Business risks for {query} include market competition, operational challenges, and financial exposure. Risk management requires "
            }
        }
        
        domain_templates = reasoning_templates.get(self.expertise, {})
        template = domain_templates.get(domain, f"As a {self.expertise} specialist, regarding {query}, ")
        
        # Add personality-specific content
        if self.personality == "conservative":
            template += "I recommend a cautious approach with thorough research and risk mitigation."
        elif self.personality == "aggressive":
            template += "I see significant opportunity here and recommend taking calculated risks for higher returns."
        else:  # balanced
            template += "I recommend a balanced approach considering both opportunities and risks."
        
        return template
    
    async def _calculate_confidence(self, query: str, domain: str) -> float:
        """Calculate agent's confidence in their response"""
        base_confidence = 75.0
        
        # Adjust based on domain expertise
        expertise_bonus = {
            "finance": {"investment": 15, "career": 10, "business": 12},
            "legal": {"career": 15, "business": 12, "investment": 8},
            "risk": {"investment": 12, "business": 15, "career": 10}
        }
        
        bonus = expertise_bonus.get(self.expertise, {}).get(domain, 5)
        
        # Add some randomness for realism
        import random
        variance = random.uniform(-5, 5)
        
        confidence = base_confidence + bonus + variance
        return max(60, min(95, confidence))  # Keep between 60-95%
    
    async def _identify_sources(self, query: str, domain: str) -> List[str]:
        """Identify data sources for the response"""
        base_sources = ["Internal knowledge base"]
        
        if domain == "investment":
            base_sources.extend(["Yahoo Finance", "SEBI regulations", "Historical market data"])
        elif domain == "career":
            base_sources.extend(["Naukri.com data", "LinkedIn insights", "Industry reports"])
        elif domain == "business":
            base_sources.extend(["Ministry of Corporate Affairs", "Industry surveys", "Market research"])
        
        return base_sources[:3]  # Return top 3 sources

class RealTimeDebateSystem:
    """Orchestrates real-time debate between multiple AI agents"""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _initialize_agents(self) -> Dict[str, DebateAgent]:
        """Initialize specialized agents for different domains"""
        return {
            "finance": DebateAgent("Finance Agent", "finance", "balanced"),
            "legal": DebateAgent("Legal Agent", "legal", "conservative"),
            "risk": DebateAgent("Risk Agent", "risk", "conservative"),
            "career": DebateAgent("Career Agent", "career", "balanced")
        }
    
    async def stream_debate(self, query: str, domain: str, user_context: Dict[str, Any] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream real-time debate between agents
        Yields agent responses as they complete thinking
        """
        
        # Select relevant agents for this domain
        relevant_agents = self._select_relevant_agents(domain)
        
        # Start all agents thinking in parallel
        agent_futures = {}
        for name, agent in relevant_agents.items():
            future = asyncio.create_task(agent.think(query, domain, user_context))
            agent_futures[name] = future
        
        # Stream responses as they complete
        completed_agents = {}
        
        while agent_futures:
            # Wait for at least one agent to complete
            done, pending = await asyncio.wait(
                agent_futures.values(),
                return_when=FIRST_COMPLETED
            )
            
            # Process completed agents
            for task in done:
                # Find which agent completed
                agent_name = None
                for name, future in agent_futures.items():
                    if future == task:
                        agent_name = name
                        break
                
                if agent_name and task not in completed_agents:
                    try:
                        response = await task
                        completed_agents[agent_name] = response
                        
                        # Stream this agent's response
                        yield {
                            "type": "agent_response",
                            "agent": agent_name,
                            "confidence": response.confidence,
                            "reasoning": response.reasoning,
                            "sources": response.sources,
                            "processing_time": response.processing_time,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Remove from pending
                        del agent_futures[agent_name]
                        
                    except Exception as e:
                        logger.error(f"Agent {agent_name} failed: {str(e)}")
                        yield {
                            "type": "agent_error",
                            "agent": agent_name,
                            "error": str(e)
                        }
        
        # Generate final synthesis
        synthesis = await self._synthesize_debate(completed_agents, query, domain)
        
        yield {
            "type": "final_synthesis",
            "synthesis": synthesis
        }
    
    def _select_relevant_agents(self, domain: str) -> Dict[str, DebateAgent]:
        """Select agents most relevant to the query domain"""
        
        agent_selection = {
            "investment": ["finance", "legal", "risk"],
            "career": ["career", "finance", "legal"],
            "business": ["finance", "legal", "risk"],
            "education": ["career", "finance"],
            "health": ["risk", "legal"],
            "immigration": ["legal", "finance"],
            "farming": ["finance", "risk"],
            "government": ["legal", "finance"]
        }
        
        selected_names = agent_selection.get(domain, ["finance", "legal"])
        return {name: self.agents[name] for name in selected_names if name in self.agents}
    
    async def _synthesize_debate(self, agent_responses: Dict[str, AgentResponse], query: str, domain: str) -> DebateSynthesis:
        """Synthesize all agent perspectives into final recommendation"""
        
        if not agent_responses:
            return DebateSynthesis(
                final_answer="I need more information to provide a proper response.",
                overall_confidence=0.0,
                agent_agreements={},
                key_insights=[],
                reasoning_summary="No agents provided input."
            )
        
        # Analyze agreements/disagreements
        agreements = {}
        confidences = [r.confidence for r in agent_responses.values()]
        
        # Find consensus (agents with similar confidence)
        avg_confidence = sum(confidences) / len(confidences)
        
        for agent_name, response in agent_responses.items():
            agreements[agent_name] = abs(response.confidence - avg_confidence) < 10
        
        # Extract key insights from all agents
        all_insights = []
        for response in agent_responses.values():
            # Extract key points from reasoning
            insights = self._extract_insights(response.reasoning)
            all_insights.extend(insights)
        
        # Generate final answer
        final_answer = await self._generate_final_answer(agent_responses, query, domain, agreements)
        
        # Calculate overall confidence
        consensus_agents = sum(1 for agree in agreements.values() if agree)
        overall_confidence = avg_confidence * (consensus_agents / len(agreements))
        
        # Create reasoning summary
        reasoning_summary = f"After considering {len(agent_responses)} perspectives, "
        reasoning_summary += f"there is {'strong' if consensus_agents >= 2 else 'mixed'} consensus. "
        reasoning_summary += f"Key factors identified: {', '.join(all_insights[:3])}."
        
        return DebateSynthesis(
            final_answer=final_answer,
            overall_confidence=overall_confidence,
            agent_agreements=agreements,
            key_insights=all_insights[:5],
            reasoning_summary=reasoning_summary
        )
    
    def _extract_insights(self, reasoning: str) -> List[str]:
        """Extract key insights from agent reasoning"""
        # Simple keyword-based extraction for now
        insights = []
        
        if "risk" in reasoning.lower():
            insights.append("Risk assessment")
        if "tax" in reasoning.lower():
            insights.append("Tax implications")
        if "return" in reasoning.lower():
            insights.append("Return potential")
        if "legal" in reasoning.lower():
            insights.append("Legal compliance")
        if "regulation" in reasoning.lower():
            insights.append("Regulatory factors")
        
        return insights[:3]  # Return top 3 insights
    
    async def _generate_final_answer(self, agent_responses: Dict[str, AgentResponse], query: str, domain: str, agreements: Dict[str, bool]) -> str:
        """Generate the final synthesized answer"""
        
        # Start with context
        answer = f"After analyzing your question about {query}, I've considered multiple perspectives:\n\n"
        
        # Add insights from agreeing agents
        agreeing_agents = [name for name, agrees in agreements.items() if agrees]
        
        if agreeing_agents:
            answer += f"The following agents agree: {', '.join(agreeing_agents)}. "
            answer += "Their key insights align on:\n"
            
            for agent_name in agreeing_agents[:2]:  # Top 2 agreeing agents
                response = agent_responses[agent_name]
                answer += f"• {response.reasoning}\n"
        
        # Add dissenting views if any
        disagreeing_agents = [name for name, agrees in agreements.items() if not agrees]
        if disagreeing_agents:
            answer += f"\nHowever, {disagreeing_agents[0]} suggests additional considerations:\n"
            answer += f"• {agent_responses[disagreeing_agents[0]].reasoning}\n"
        
        # Final recommendation
        answer += f"\n**My Recommendation:**\n"
        
        if domain == "investment":
            answer += "Based on the consensus, I recommend a balanced approach with proper risk management."
        elif domain == "career":
            answer += "The analysis suggests focusing on skill development while considering financial implications."
        elif domain == "business":
            answer += "I recommend proceeding with proper legal compliance and risk mitigation strategies."
        else:
            answer += "I recommend careful consideration of all factors mentioned above."
        
        return answer

# Global debate system instance
debate_system = RealTimeDebateSystem()
