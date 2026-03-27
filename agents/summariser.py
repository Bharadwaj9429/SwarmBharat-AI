from crewai import Agent
from prompts import SUMMARISER_PROMPT

summariser = Agent(
    role="Voice Summariser",
    goal="Convert the entire output into a clear, short voice summary",
    backstory=SUMMARISER_PROMPT,
    verbose=True,
    allow_delegation=False
)