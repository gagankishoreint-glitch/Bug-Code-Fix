import os
from datetime import datetime
import sqlite3
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

DB_NAME="cofix-history.db"

def init_db():
    """create a database for the ollama model to store the fixes and overwrite the buggy file"""
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
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

@tool
def read_file(file_path:str)-> str:
    """Reads and returns the text content of the given file path."""
    if not os.path.exists(file_path):
        return f"Error: File {file_path} does not exist"
    with open(file_path,"r") as f:
        return f.read()
    
@tool
def save_and_log(file_path:str,bug_summary:str,fixed_code:str)-> str:
    """Saves the corrected code to the file AND logs the bug details in SQLite"""
    with open(file_path,"w") as f:
        f.write(fixed_code)

    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute('''INSERT INTO review_history (file_path, bug_summary, fixed_code, timestamp)
        VALUES (?, ?, ?, ?)''',(file_path,bug_summary,fixed_code,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return f"Successfully updated '{file_path}'!"

@tool
def fix_history(file_path: str) -> str:
    """Queries the SQLite database for past bug fixes applied to a specific file."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, bug_summary, timestamp FROM review_history WHERE file_path = ? ORDER BY id DESC
    ''', (file_path,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"no prior history or data found for '{file_path}'."
    history_report = f"Fix History for '{file_path}':\n"
    for row in rows:
        history_report += f"- [ID {row[0]} | {row[2]}] Summary: {row[1]}\n"
    return history_report


#agent-setup
llm=ChatOllama(model="llama3.2",temperature=0)

system_prompt=("You are an expert Python Bug Hunter agent. "
    "Use `read_file` to read files. "
    "When applying fixes, use `save_and_log` to overwrite the file and record the entry in DB. "
    "Use `fix_history` if the user asks about previous logs.")

agent=create_react_agent(
    llm,
    tools=[read_file,save_and_log,fix_history],
    prompt=system_prompt
)
print("\n Bug Hunter Agent (Type 'exit' to quit)\n" + "-"*50)

while True:
    user_input = input("\nEnter request: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    
    response = agent.invoke({"messages": [("user", user_input)]})
    print("\nAgent Response:\n", response["messages"][-1].content)