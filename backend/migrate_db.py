import os
import sqlite3

db_path = "recorder_v5.db"

if os.path.exists(db_path):
    print(f"Connecting to {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if columns exist
    cursor.execute("PRAGMA table_info(agents)")
    columns = [info[1] for info in cursor.fetchall()]

    if "skills_config" not in columns:
        print("Adding skills_config column...")
        try:
            cursor.execute("ALTER TABLE agents ADD COLUMN skills_config JSON")
            print("Added skills_config")
        except Exception as e:
            print(f"Error adding skills_config: {e}")

    if "mcp_config" not in columns:
        print("Adding mcp_config column...")
        try:
            cursor.execute("ALTER TABLE agents ADD COLUMN mcp_config JSON")
            print("Added mcp_config")
        except Exception as e:
            print(f"Error adding mcp_config: {e}")

    # Check LLMModel table
    cursor.execute("PRAGMA table_info(llm_models)")
    llm_columns = [info[1] for info in cursor.fetchall()]

    if "model_type" not in llm_columns:
        print("Adding model_type column to llm_models...")
        try:
            cursor.execute("ALTER TABLE llm_models ADD COLUMN model_type VARCHAR DEFAULT 'text'")
            print("Added model_type")
        except Exception as e:
            print(f"Error adding model_type: {e}")

    # Create Chat Tables if not exist
    print("Creating chat tables if not exist...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            user_id VARCHAR,
            agent_id VARCHAR,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(agent_id) REFERENCES agents(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR NOT NULL,
            role VARCHAR NOT NULL,
            content TEXT NOT NULL,
            message_type VARCHAR DEFAULT 'text',
            meta_data JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )
        """)
        print("Chat tables checked/created")
    except Exception as e:
        print(f"Error creating chat tables: {e}")

    # Create Workflow Table
    print("Creating workflow table if not exist...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            description VARCHAR,
            webhook_url VARCHAR NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Workflow table checked/created")
    except Exception as e:
        print(f"Error creating workflow table: {e}")

    conn.commit()
    conn.close()
else:
    print(f"Database {db_path} not found.")
