from crewai import Agent
from prompts import RESEARCHER_PROMPT

researcher = Agent(
    role="Researcher",
    goal="Find accurate and latest information",
    backstory=RESEARCHER_PROMPT,
    verbose=True,
    allow_delegation=False
)