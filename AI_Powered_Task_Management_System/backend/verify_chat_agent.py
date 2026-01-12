import sys
import os

sys.path.append(os.getcwd())

try:
    from app.agents.chat_agent import chat_agent
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
