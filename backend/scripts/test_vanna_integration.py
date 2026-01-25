import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.vanna.models import DbConnectionConfig
from app.services.vanna.service import SmartDataQueryService

def test_integration():
    print("Testing Smart Data Query Integration...")
    
    # 1. Initialize Service
    service = SmartDataQueryService.get_instance()
    print("Service initialized.")
    
    # 2. Mock Connection (using SQLite in-memory or a dummy file)
    config = DbConnectionConfig(
        type="sqlite",
        path="test_vanna.db"
    )
    
    # Create dummy db
    import sqlite3
    with sqlite3.connect("test_vanna.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, item TEXT, amount REAL)")
        conn.execute("INSERT INTO sales (item, amount) VALUES ('Apple', 100.0)")
        conn.execute("INSERT INTO sales (item, amount) VALUES ('Banana', 50.0)")
        conn.commit()
        
    try:
        service.connect_db(config)
        print("Database connected.")
        
        # 3. Test Agent Initialization (Mocking LLM to avoid API call if possible, or just checking object)
        # We can't easily mock the LLM call without API key, but we can check if agent is created.
        if service.agent:
            print("Agent created.")
            
            # Check tools
            print(f"Tools: {[t.__name__ for t in service.agent.tools]}")
            
        else:
            print("Agent creation failed (might be due to missing API key, which is expected in test env).")

    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        # Cleanup
        if os.path.exists("test_vanna.db"):
            os.remove("test_vanna.db")

if __name__ == "__main__":
    test_integration()
