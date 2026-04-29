"""
SwarmBharat Action Tracker & Proactive Intelligence
Tracks user commitments, sends reminders, triggers proactive alerts
This is what makes users actually follow through (no AI does this)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReminderType(str, Enum):
    """Types of reminders"""
    COMMITMENT = "commitment"  # User committed to something
    MILESTONE = "milestone"    # Scheduled milestone
    ALERT = "alert"           # Important information
    OPPORTUNITY = "opportunity"  # Time-sensitive opportunity
    FOLLOW_UP = "follow_up"   # Check-in with user


class ProactiveAlert:
    """
    Monitors user's interests and triggers alerts when relevant
    E.g., user interested in Canada PR → alert when Express Entry draw happens
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.alerts = []
        self.last_check = datetime.now()
    
    async def check_farming_alerts(self, user_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for farming-related alerts"""
        alerts = []
        
        farming_info = user_memory.get("farming", {})
        if not farming_info.get("is_farmer"):
            return alerts
        
        district = farming_info.get("district")
        
        # Check weather alerts
        # In production: fetch actual weather data
        weather_alert = {
            "type": ReminderType.ALERT,
            "domain": "farming",
            "title": "⚠️ Low rainfall alert",
            "description": f"Rainfall in {district} below normal levels. PM Fasal Bima Yojana claim window opens in 15 days.",
            "action_url": "https://pmfby.gov.in/",
            "deadline": (datetime.now() + timedelta(days=15)).isoformat(),
            "priority": "high"
        }
        alerts.append(weather_alert)
        
        # Check scheme payment dates
        scheme_alert = {
            "type": ReminderType.MILESTONE,
            "domain": "farming",
            "title": "💰 Rythu Bandhu Rabi payment expected",
            "description": "Based on previous payment patterns, Rabi season payment expected this week",
            "action": "Check payment status at https://rythu.telangana.gov.in",
            "date": datetime.now().isoformat(),
            "priority": "medium"
        }
        alerts.append(scheme_alert)
        
        return alerts
    
    async def check_career_alerts(self, user_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for career/job alerts"""
        alerts = []
        
        career_info = user_memory.get("career", {})
        if not career_info.get("job_hunting"):
            return alerts
        
        target_role = career_info.get("target_role")
        city = user_memory.get("personal", {}).get("city")
        
        if not target_role or not city:
            return alerts
        
        # Check for new job postings
        # In production: fetch from Naukri API
        job_alert = {
            "type": ReminderType.OPPORTUNITY,
            "domain": "career",
            "title": f"🎯 3 new {target_role} jobs in {city}",
            "description": "Companies matching your profile just posted: TCS (₹15L), Wipro (₹16L), Infosys (₹14.5L)",
            "action": "View & apply on Naukri",
            "deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": "high"
        }
        alerts.append(job_alert)
        
        # Check salary growth opportunity
        experience = career_info.get("experience_years", 0)
        if experience >= 3:
            salary_alert = {
                "type": ReminderType.MILESTONE,
                "domain": "career",
                "title": "💼 You're eligible for senior roles",
                "description": f"With {experience} years experience, you're now entering senior bracket (20% higher pay). Market rate: ₹18-22L for your profile.",
                "action": "Update resume & apply",
                "date": datetime.now().isoformat(),
                "priority": "medium"
            }
            alerts.append(salary_alert)
        
        return alerts
    
    async def check_immigration_alerts(self, user_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for immigration opportunity alerts"""
        alerts = []
        
        imm_info = user_memory.get("immigration", {})
        if not imm_info.get("interested"):
            return alerts
        
        target_country = imm_info.get("target_country")
        crs_score = imm_info.get("crs_score")
        
        if target_country == "Canada" and crs_score:
            # Check latest Express Entry draw
            # In production: fetch real data from IRCC
            draw_alert = {
                "type": ReminderType.OPPORTUNITY,
                "domain": "immigration",
                "title": "🚨 Express Entry draw happened!",
                "description": f"Latest draw cutoff: 491. Your score: {crs_score}. YOU QUALIFY! ✅ Apply within 60 days.",
                "action": "Start Express Entry application",
                "deadline": (datetime.now() + timedelta(days=60)).isoformat(),
                "priority": "critical",
                "action_url": "https://www.canada.ca/en/immigration-refugees-citizenship"
            }
            alerts.append(draw_alert)
        
        return alerts
    
    async def check_finance_alerts(self, user_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for finance-related alerts"""
        alerts = []
        
        finance_info = user_memory.get("finance", {})
        income = finance_info.get("annual_income")
        
        if income and income < 500000:  # Below 5L per year
            scheme_alert = {
                "type": ReminderType.OPPORTUNITY,
                "domain": "finance",
                "title": "💰 You qualify for 6 government schemes",
                "description": "Ayushman Bharat (₹5L health cover), PM Kisan (₹6K/year), Sukanya if you have daughter...",
                "action": "Check eligibility & claim",
                "priority": "high",
                "annual_value": "₹24,000"
            }
            alerts.append(scheme_alert)
        
        return alerts
    
    async def check_health_alerts(self, user_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for health-related alerts"""
        alerts = []
        
        health_info = user_memory.get("health", {})
        age_group = health_info.get("age_group")
        conditions = health_info.get("conditions", [])
        
        # Age-based preventive care
        if age_group == "40-50":
            checkup_alert = {
                "type": ReminderType.MILESTONE,
                "domain": "health",
                "title": "🏥 Annual health checkup due",
                "description": "Recommended annual checkup for age 40+: blood pressure, cholesterol, blood sugar, etc.",
                "action": "Book appointment",
                "priority": "medium",
                "providers": "Aarogyasri hospitals (free/subsidized)"
            }
            alerts.append(checkup_alert)
        
        # Condition-based reminders
        if "diabetes" in conditions:
            medication_alert = {
                "type": ReminderType.REMINDER,
                "domain": "health",
                "title": "💊 Medication refill due",
                "description": "Based on previous refill pattern, time to order diabetes medication",
                "action": "Contact doctor/pharmacy",
                "priority": "high"
            }
            alerts.append(medication_alert)
        
        return alerts
    
    async def get_all_proactive_alerts(self, user_memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all relevant alerts for user"""
        all_alerts = []
        
        # Check each domain
        all_alerts.extend(await self.check_farming_alerts(user_memory))
        all_alerts.extend(await self.check_career_alerts(user_memory))
        all_alerts.extend(await self.check_immigration_alerts(user_memory))
        all_alerts.extend(await self.check_finance_alerts(user_memory))
        all_alerts.extend(await self.check_health_alerts(user_memory))
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_alerts.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 99))
        
        self.alerts = all_alerts
        self.last_check = datetime.now()
        
        logger.info(f"✓ Generated {len(all_alerts)} proactive alerts for user {self.user_id}")
        return all_alerts
    
    async def format_for_notification(self, alert: Dict[str, Any]) -> str:
        """Format alert for push notification or message"""
        
        emoji = {
            "farming": "🌾",
            "career": "💼",
            "immigration": "✈️",
            "finance": "💰",
            "health": "🏥",
            "legal": "⚖️"
        }
        
        domain_emoji = emoji.get(alert.get("domain"), "📢")
        
        notification = f"""{domain_emoji} {alert.get('title', 'Update')}

{alert.get('description', '')}

Action: {alert.get('action', 'Check app for details')}"""
        
        if alert.get("deadline"):
            deadline = datetime.fromisoformat(alert["deadline"])
            days_left = (deadline - datetime.now()).days
            if days_left > 0:
                notification += f"\n\n⏰ {days_left} days remaining"
        
        return notification


class ActionTracker:
    """
    Tracks user commitments and follows up
    This is what ensures users actually take action
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.actions = []
        self.completed = 0
        self.skipped = 0
    
    async def add_action(self, action: str, deadline: datetime, domain: str,
                        parent_goal: str = None) -> bool:
        """Track a new action user committed to"""
        
        action_record = {
            "id": f"{self.user_id}_{len(self.actions)}_{datetime.now().timestamp()}",
            "action": action,
            "deadline": deadline.isoformat(),
            "domain": domain,
            "parent_goal": parent_goal,
            "status": "pending",  # pending, in_progress, completed, skipped
            "created_at": datetime.now().isoformat(),
            "reminders_sent": [],
            "blocked_reason": None,
            "notes": ""
        }
        
        self.actions.append(action_record)
        logger.info(f"✓ Action tracked: {action}")
        return True
    
    async def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all incomplete actions"""
        return [a for a in self.actions if a["status"] == "pending"]
    
    async def get_actions_due_soon(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get actions due in next N days"""
        soon = []
        cutoff = datetime.now() + timedelta(days=days)
        
        for action in self.actions:
            if action["status"] == "pending":
                deadline = datetime.fromisoformat(action["deadline"])
                if datetime.now() < deadline < cutoff:
                    soon.append(action)
        
        return sorted(soon, key=lambda x: x["deadline"])
    
    async def get_overdue_actions(self) -> List[Dict[str, Any]]:
        """Get actions that missed deadline"""
        overdue = []
        
        for action in self.actions:
            if action["status"] == "pending":
                deadline = datetime.fromisoformat(action["deadline"])
                if deadline < datetime.now():
                    overdue.append(action)
        
        return sorted(overdue, key=lambda x: x["deadline"], reverse=True)
    
    async def mark_action_done(self, action_id: str) -> Dict[str, Any]:
        """Mark action as complete"""
        
        for action in self.actions:
            if action["id"] == action_id:
                action["status"] = "completed"
                action["completed_at"] = datetime.now().isoformat()
                self.completed += 1
                
                # Celebration message
                celebration = {
                    "status": "success",
                    "message": f"🎉 Amazing! You completed: {action['action']}",
                    "next_step_suggestion": await self._suggest_next_step(action)
                }
                
                logger.info(f"✓ Action completed: {action['action']}")
                return celebration
        
        return {"status": "error", "message": "Action not found"}
    
    async def _suggest_next_step(self, completed_action: Dict[str, Any]) -> str:
        """Suggest next logical step after completing an action"""
        
        suggestions = {
            "resume": "Next: Add your achievements to LinkedIn profile",
            "interview": "Next: Follow up email in 24 hours",
            "application": "Next: Check application portal in 3 days",
            "exam": "Next: Review weak areas from results",
            "training": "Next: Implement what you learned"
        }
        
        for keyword, suggestion in suggestions.items():
            if keyword in completed_action["action"].lower():
                return suggestion
        
        return "Next: Check app for more steps in this area"
    
    async def send_reminder(self, action_id: str) -> Dict[str, str]:
        """Send reminder for specific action"""
        
        for action in self.actions:
            if action["id"] == action_id and action["status"] == "pending":
                
                deadline = datetime.fromisoformat(action["deadline"])
                days_left = (deadline - datetime.now()).days
                
                if days_left < 0:
                    reminder = f"""
⏰ OVERDUE: {action['action']}

This was due {abs(days_left)} days ago. 

✗ Blocked? Let me help you get unstuck.
✓ Done? Mark it as complete.
→ Need more time? Let's adjust the plan.
                    """
                
                elif days_left == 0:
                    reminder = f"""
🚨 TODAY: {action['action']}

This needs to be done today!

Focus area: {action['domain']}
Goal: {action['parent_goal'] or 'General progress'}

You've got this! 💪
                    """
                
                else:
                    reminder = f"""
📅 REMINDER: {action['action']}

Due in {days_left} day(s)

Take 5 minutes today to get started?
                    """
                
                # Track that reminder was sent
                action["reminders_sent"].append(datetime.now().isoformat())
                
                return {
                    "action_id": action_id,
                    "reminder": reminder,
                    "days_left": days_left
                }
        
        return {"error": "Action not found"}
    
    async def mark_action_blocked(self, action_id: str, reason: str) -> bool:
        """Mark action as blocked - user needs help"""
        
        for action in self.actions:
            if action["id"] == action_id:
                action["status"] = "blocked"
                action["blocked_reason"] = reason
                
                # Trigger help response
                help_message = f"""
🆘 I see you're stuck on: {action['action']}

Reason: {reason}

Let me help. Tell me:
1. What specifically is blocking you?
2. Have you tried anything so far?
3. What would unstick this?

We'll figure it out together. You're not alone in this.
                """
                
                logger.info(f"⚠️  Action blocked: {action['action']} - {reason}")
                return True
        
        return False
    
    async def get_action_success_stats(self) -> Dict[str, Any]:
        """Get user's action completion stats"""
        
        total = len(self.actions)
        completed = len([a for a in self.actions if a["status"] == "completed"])
        pending = len([a for a in self.actions if a["status"] == "pending"])
        blocked = len([a for a in self.actions if a["status"] == "blocked"])
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            "total_actions": total,
            "completed": completed,
            "pending": pending,
            "blocked": blocked,
            "completion_rate": f"{completion_rate:.1f}%",
            "streak": await self._calculate_streak(),
            "consistency": "improving" if completion_rate > 70 else "developing"
        }
    
    async def _calculate_streak(self) -> int:
        """Calculate consecutive days with completed actions"""
        if not self.actions:
            return 0
        
        completed = sorted(
            [a for a in self.actions if a["status"] == "completed"],
            key=lambda x: x.get("completed_at", ""),
            reverse=True
        )
        
        streak = 0
        today = datetime.now().date()
        
        for action in completed:
            completed_date = datetime.fromisoformat(action.get("completed_at", "")).date()
            expected_date = today - timedelta(days=streak)
            
            if completed_date == expected_date:
                streak += 1
            else:
                break
        
        return streak
