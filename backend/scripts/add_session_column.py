import os
import sqlite3

db_path = "recorder_v5.db"

if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(0)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(knowledge_chats)")
    columns = [info[1] for info in cursor.fetchall()]

    if "session_id" not in columns:
        print("Adding session_id column to knowledge_chats...")
        cursor.execute("ALTER TABLE knowledge_chats ADD COLUMN session_id TEXT")
        # Add index
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_chats_session_id ON knowledge_chats (session_id)")
        conn.commit()
        print("Done.")
    else:
        print("Column session_id already exists.")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
