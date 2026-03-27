from crewai import Agent
from prompts import MENTOR_PROMPT

mentor = Agent(
    role="Mentor",
    goal="Create simple step-by-step action plans and ready-to-use messages",
    backstory=MENTOR_PROMPT,
    verbose=True,
    allow_delegation=False
)