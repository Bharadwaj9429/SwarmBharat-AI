from crewai import Agent
from prompts import RISK_PROMPT

risk_simulator = Agent(
    role="Risk & Simulator",
    goal="Run what-if scenarios and calculate risks",
    backstory=RISK_PROMPT,
    verbose=True,
    allow_delegation=False
)