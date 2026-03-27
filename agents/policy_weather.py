from crewai import Agent
from prompts import POLICY_PROMPT

policy_weather = Agent(
    role="Policy & Weather Expert",
    goal="Explain government schemes and weather in simple language",
    backstory=POLICY_PROMPT,
    verbose=True,
    allow_delegation=False
)