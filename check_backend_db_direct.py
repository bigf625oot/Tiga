
import sqlite3
import sys
from pathlib import Path

# Path to the backend DB
db_path = Path("backend/recorder_v5.db")

if not db_path.exists():
    print(f"Error: {db_path} does not exist!")
    sys.exit(1)

print(f"Checking database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n--- Active LLM Models (type != embedding) ---")
    cursor.execute("SELECT id, name, model_id, is_active FROM llm_models WHERE is_active = 1 AND model_type != 'embedding'")
    rows = cursor.fetchall()
    for r in rows:
        print(r)

    print("\n--- Active Embedding Models (type == embedding) ---")
    cursor.execute("SELECT id, name, model_id, is_active FROM llm_models WHERE is_active = 1 AND model_type = 'embedding'")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
        
    print("\n--- All Models ---")
    cursor.execute("SELECT id, name, model_id, model_type, is_active FROM llm_models")
    rows = cursor.fetchall()
    for r in rows:
        print(r)

    conn.close()

except Exception as e:
    print(f"Error: {e}")
