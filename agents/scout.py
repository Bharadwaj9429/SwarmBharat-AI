from crewai import Agent
from prompts import SCOUT_PROMPT

scout = Agent(
    role="Local Scout",
    goal="Find real local jobs, markets, farmers or match internal company resources",
    backstory=SCOUT_PROMPT,
    verbose=True,
    allow_delegation=False
)