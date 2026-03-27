"""
SwarmBharat AI — FastAPI backend
Fixed: CORS credentials bug, Form() endpoint, proper response keys
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from crewai import Crew, Agent, Task
import uvicorn
import os
from PyPDF2 import PdfReader
import io

load_dotenv()

app = FastAPI(title="SwarmBharat AI")

# ── CORS FIX: allow_credentials must be False when allow_origins=["*"] ────────
# Chrome rejects credentials=True + wildcard origin. This was silently blocking
# every request before it even reached your route handler.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # <-- CRITICAL FIX (was True, Chrome blocks that)
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "SwarmBharat AI is running!"}

# ── MAIN ENDPOINT: accepts Form data (multipart) for file upload support ──────
@app.post("/swarm")
async def run_swarm(
    query: str = Form(...),
    mode: str = Form("personal"),
    file: UploadFile = File(None)
):
    try:
        resume_text = ""

        # Handle uploaded PDF
        if file and file.filename and file.filename.endswith(".pdf"):
            content = await file.read()
            pdf = PdfReader(io.BytesIO(content))
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    resume_text += text + "\n"
            resume_text = f"\n\nUser uploaded resume/document:\n{resume_text[:4000]}"

        full_query = f"{query}{resume_text}"

        # Groq model — fast and free tier
        llm_model = "groq/llama-3.3-70b-versatile"

        # Build agents
        researcher    = Agent(role="Researcher",     goal="Find accurate information",              backstory="You are a Researcher Agent.",          llm=llm_model, verbose=False)
        accountant    = Agent(role="Accountant",     goal="Calculate costs and savings",            backstory="You are an Accountant Agent.",          llm=llm_model, verbose=False)
        scout         = Agent(role="Local Scout",    goal="Find local options in Telangana/India",  backstory="You are a Local Scout Agent.",           llm=llm_model, verbose=False)
        mentor        = Agent(role="Mentor",         goal="Give clear step-by-step plan",           backstory="You are a Mentor Agent.",               llm=llm_model, verbose=False)
        risk_sim      = Agent(role="Risk Simulator", goal="Identify and explain risks",             backstory="You are a Risk Simulator Agent.",        llm=llm_model, verbose=False)
        policy_expert = Agent(role="Policy Expert",  goal="Explain government schemes simply",      backstory="You are a Policy and Weather Agent.",    llm=llm_model, verbose=False)
        summariser    = Agent(role="Summariser",     goal="Give short clear summary in Telugu/Hindi/English", backstory="You are a Voice Summariser Agent.", llm=llm_model, verbose=False)

        task = Task(
            description=(
                f"Give a practical, helpful, step-by-step answer to this query: {full_query}\n\n"
                f"Mode: {mode}. "
                f"If mode is 'personal', answer for farmers, students, or daily workers in simple language. "
                f"Use Telugu, Hindi, or English based on the question language."
            ),
            agent=mentor,
            expected_output="A clear, practical, step-by-step answer."
        )

        crew = Crew(
            agents=[researcher, accountant, scout, mentor, risk_sim, policy_expert, summariser],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()

        # Return with key "response" — matches what Flutter reads
        return {
            "status": "success",
            "response": str(result)
        }

    except Exception as e:
        return {
            "status": "error",
            "response": f"Sorry, an error occurred: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)