from crewai import Agent
from prompts import ACCOUNTANT_PROMPT

accountant = Agent(
    role="Accountant",
    goal="Calculate realistic cash-only costs and savings",
    backstory=ACCOUNTANT_PROMPT,
    verbose=True,
    allow_delegation=False
)