import os
import sqlite3

# Path to database file (in project root)
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recorder_v5.db")

if os.path.exists(db_path):
    print(f"Connecting to {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check columns for chat_sessions
    cursor.execute("PRAGMA table_info(chat_sessions)")
    columns = [info[1] for info in cursor.fetchall()]

    if "mode" not in columns:
        print("Adding mode column to chat_sessions...")
        try:
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN mode VARCHAR DEFAULT 'chat'")
            print("Added mode")
        except Exception as e:
            print(f"Error adding mode to chat_sessions: {e}")
    else:
        print("mode column already exists in chat_sessions")

    conn.commit()
    conn.close()
else:
    print(f"Database {db_path} not found.")
