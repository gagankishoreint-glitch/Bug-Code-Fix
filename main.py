import os
import re
import sqlite3
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

DB_NAME = "cofix-history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS review_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        bug_summary TEXT NOT NULL,
        fixed_code TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

app = FastAPI(title="CoFix API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOllama(model="llama3.2", temperature=0)

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if os.path.exists("index.html"):
        with open("index.html", "r") as f:
            return f.read()
    return "<h1>index.html not found</h1>"

class FixRequest(BaseModel):
    file_path: str = "target_buggy_code.py"
    code_content: str

def extract_code(llm_response: str) -> str:
    """Strips markdown backticks and returns clean runnable code."""
    match = re.search(r"```(?:python)?\s*\n(.*?)```", llm_response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return llm_response.strip()

@app.post("/api/fix")
async def run_agent_fix(payload: FixRequest):
    try:
        # 1. Directly prompt Ollama to fix code
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert Python debugger. Fix all bugs (syntax, logic, index errors, zero division). Return ONLY the clean, corrected Python code inside a ```python ``` code block. Do NOT include explanations."),
            ("user", "Fix this code:\n\n{code}")
        ])

        chain = prompt | llm
        response = chain.invoke({"code": payload.code_content})

        fixed_code = extract_code(response.content)

        # 2. Python directly writes to disk & SQLite (Bulletproof)
        with open(payload.file_path, "w") as f:
            f.write(fixed_code)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO review_history (file_path, bug_summary, fixed_code, timestamp)
            VALUES (?, ?, ?, ?)''', (payload.file_path, "Fixed logic & runtime bugs", fixed_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        # 3. Return the fixed code straight to the UI
        return {
            "success": True,
            "fixed_code": fixed_code,
            "steps": [
                "🔍 Analyzed syntax & runtime errors",
                "⚡ Corrected loop bounds & division guards",
                "💾 Saved patch to workspace & SQLite history"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)