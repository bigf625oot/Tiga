import os
import sqlite3

# Path to database file (in project root)
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recorder_v5.db")

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

    # [FIX] Add 'role' column if missing
    if "role" not in columns:
        print("Adding role column...")
        try:
            cursor.execute("ALTER TABLE agents ADD COLUMN role VARCHAR DEFAULT 'general'")
            print("Added role")
        except Exception as e:
            print(f"Error adding role: {e}")

    # --- Skills Table ---
    print("Checking skills table...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            description VARCHAR,
            version VARCHAR DEFAULT '1.0.0',
            content TEXT,
            tools_config JSON,
            meta_data JSON,
            category VARCHAR,
            author VARCHAR DEFAULT 'System',
            is_official BOOLEAN DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Check columns for skills (for existing tables)
        cursor.execute("PRAGMA table_info(skills)")
        skill_cols = [info[1] for info in cursor.fetchall()]
        
        new_skill_cols = {
            "category": "VARCHAR",
            "author": "VARCHAR DEFAULT 'System'",
            "is_official": "BOOLEAN DEFAULT 0",
            "downloads": "INTEGER DEFAULT 0"
        }
        
        for col, dtype in new_skill_cols.items():
            if col not in skill_cols:
                print(f"Adding {col} to skills...")
                try:
                    cursor.execute(f"ALTER TABLE skills ADD COLUMN {col} {dtype}")
                except Exception as e:
                    print(f"Error adding {col} to skills: {e}")
                    
        print("Skills table checked/created")
    except Exception as e:
        print(f"Error checking/creating skills table: {e}")

    # --- MCP Servers Table ---
    print("Checking mcp_servers table...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mcp_servers (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            description VARCHAR,
            type VARCHAR NOT NULL,
            config JSON NOT NULL,
            category VARCHAR,
            author VARCHAR DEFAULT 'User',
            is_official BOOLEAN DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Check columns for mcp_servers
        cursor.execute("PRAGMA table_info(mcp_servers)")
        mcp_cols = [info[1] for info in cursor.fetchall()]
        
        new_mcp_cols = {
            "version": "VARCHAR DEFAULT '1.0.0'",
            "category": "VARCHAR",
            "author": "VARCHAR DEFAULT 'User'",
            "is_official": "BOOLEAN DEFAULT 0",
            "downloads": "INTEGER DEFAULT 0"
        }
        
        for col, dtype in new_mcp_cols.items():
            if col not in mcp_cols:
                print(f"Adding {col} to mcp_servers...")
                try:
                    cursor.execute(f"ALTER TABLE mcp_servers ADD COLUMN {col} {dtype}")
                except Exception as e:
                    print(f"Error adding {col} to mcp_servers: {e}")

        print("MCP Servers table checked/created")
    except Exception as e:
        print(f"Error checking/creating mcp_servers table: {e}")

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

    # Check KnowledgeDocument table
    cursor.execute("PRAGMA table_info(knowledge_documents)")
    kd_columns = [info[1] for info in cursor.fetchall()]

    if "is_folder" not in kd_columns:
        print("Adding is_folder column to knowledge_documents...")
        try:
            cursor.execute("ALTER TABLE knowledge_documents ADD COLUMN is_folder BOOLEAN DEFAULT 0")
            print("Added is_folder")
        except Exception as e:
            print(f"Error adding is_folder: {e}")

    if "parent_id" not in kd_columns:
        print("Adding parent_id column to knowledge_documents...")
        try:
            cursor.execute("ALTER TABLE knowledge_documents ADD COLUMN parent_id INTEGER")
            print("Added parent_id")
        except Exception as e:
            print(f"Error adding parent_id: {e}")

    # Check Recordings table
    cursor.execute("PRAGMA table_info(recordings)")
    rec_columns = [info[1] for info in cursor.fetchall()]

    if "transcription_json" not in rec_columns:
        print("Adding transcription_json column to recordings...")
        try:
            cursor.execute("ALTER TABLE recordings ADD COLUMN transcription_json TEXT")
            print("Added transcription_json")
        except Exception as e:
            print(f"Error adding transcription_json: {e}")

    if "is_deleted" not in kd_columns:
        print("Adding is_deleted column to knowledge_documents...")
        try:
            cursor.execute("ALTER TABLE knowledge_documents ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
            print("Added is_deleted")
        except Exception as e:
            print(f"Error adding is_deleted: {e}")

    if "deleted_at" not in kd_columns:
        print("Adding deleted_at column to knowledge_documents...")
        try:
            cursor.execute("ALTER TABLE knowledge_documents ADD COLUMN deleted_at DATETIME")
            print("Added deleted_at")
        except Exception as e:
            print(f"Error adding deleted_at: {e}")

    # Create Chat Tables if not exist
    print("Creating chat tables if not exist...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            user_id VARCHAR,
            agent_id VARCHAR,
            workflow_state JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(agent_id) REFERENCES agents(id)
        )
        """)

        # Check columns for chat_sessions
        cursor.execute("PRAGMA table_info(chat_sessions)")
        chat_session_cols = [info[1] for info in cursor.fetchall()]

        if "workflow_state" not in chat_session_cols:
            print("Adding workflow_state to chat_sessions...")
            try:
                cursor.execute("ALTER TABLE chat_sessions ADD COLUMN workflow_state JSON")
                print("Added workflow_state")
            except Exception as e:
                print(f"Error adding workflow_state to chat_sessions: {e}")

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

    print("Creating task mode tables if not exist...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            description_enc TEXT,
            status VARCHAR NOT NULL DEFAULT 'open',
            priority INTEGER NOT NULL DEFAULT 3,
            assignee_id VARCHAR,
            created_by VARCHAR,
            current_version INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(assignee_id) REFERENCES users(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tasks_name ON tasks(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tasks_priority ON tasks(priority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tasks_assignee_id ON tasks(assignee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tasks_created_by ON tasks(created_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tasks_created_at ON tasks(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_tasks_updated_at ON tasks(updated_at)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id VARCHAR NOT NULL,
            version INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            description_enc TEXT,
            status VARCHAR NOT NULL,
            priority INTEGER NOT NULL,
            assignee_id VARCHAR,
            changed_by VARCHAR,
            change_summary VARCHAR,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES tasks(id),
            FOREIGN KEY(assignee_id) REFERENCES users(id),
            FOREIGN KEY(changed_by) REFERENCES users(id)
        )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_task_versions_task_version ON task_versions(task_id, version)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_versions_task_id ON task_versions(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_versions_version ON task_versions(version)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_versions_created_at ON task_versions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_versions_changed_by ON task_versions(changed_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_versions_assignee_id ON task_versions(assignee_id)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_qas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id VARCHAR NOT NULL,
            user_id VARCHAR,
            question_enc TEXT NOT NULL,
            answer_enc TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES tasks(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_qas_task_id ON task_qas(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_qas_user_id ON task_qas(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_qas_created_at ON task_qas(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_qas_updated_at ON task_qas(updated_at)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id VARCHAR NOT NULL,
            actor_id VARCHAR,
            action_type VARCHAR NOT NULL,
            importance VARCHAR NOT NULL DEFAULT 'normal',
            content_enc TEXT,
            before_state_enc TEXT,
            after_state_enc TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            FOREIGN KEY(task_id) REFERENCES tasks(id),
            FOREIGN KEY(actor_id) REFERENCES users(id)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_logs_task_id ON task_logs(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_logs_actor_id ON task_logs(actor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_logs_action_type ON task_logs(action_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_logs_importance ON task_logs(importance)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_logs_created_at ON task_logs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_task_logs_expires_at ON task_logs(expires_at)")

        print("Task mode tables checked/created")
    except Exception as e:
        print(f"Error creating task mode tables: {e}")

    conn.commit()
    conn.close()
else:
    print(f"Database {db_path} not found.")
