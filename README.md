# 🤖 Bug-Code-Fix (Code Review Agent)

A lightweight local AI agent built with **LangGraph**, **LangChain**, **Ollama**, and **SQLite**. It reads Python scripts, spots logic and syntax bugs, rewrites the code, and logs every fix to a local database.

---

## ⚠️ Work in Progress (Known Issue)

**Heads up:** This project is an active experiment! 

Right now, smaller local LLMs (like `llama3.2`) occasionally get lazy during tool calling. Instead of passing the full, fixed Python code back into the `save_and_log` function, the model sometimes outputs placeholder strings (like `<your_fixed_code>`) or skips returning the updated code entirely.

### What's being worked on next:
* **Stricter Prompting:** Forcing local models to always pass valid, non-placeholder code to tools.
* **Code Execution Loop:** Adding a script-runner tool so the agent can execute the Python code, read terminal errors, and auto-test its own fixes before saving.
* **Vector DB / Context:** Upgrading memory so it can analyze full folders instead of single files.

---

## 🛠️ How It Works

The agent currently relies on 3 custom tools:
1. `read_file`: Reads target Python files in your workspace.
2. `save_and_log`: Overwrites buggy files with corrected code and logs timestamps + summaries into `cofix-history.db`.
3. `fix_history`: Queries SQLite to show past fixes applied to any file.

---

## 🚀 How to Run

1. **Activate your environment: **
   ```bash
   source venv/bin/activate
2. **Ensure Ollama is running locally :**
    ```Bash
    ollama run llama3.2
3. **run the agent :**
   ```python
     python main.py

**Techstack:**
LLM: Ollama (llama3.2)
Agent Framework: LangChain & LangGraph
Database: SQLite
