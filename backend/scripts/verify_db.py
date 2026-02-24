import sqlite3
import os

# Path to database file (in project root)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recorder_v5.db")

def verify():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} does not exist!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tables we expect to have data
    tables = ["agents", "skills", "mcp_servers", "llm_models"]
    print(f"Checking data in {DB_PATH}...")
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Table '{table}': {count} rows")
            
            # Print names for verification
            cursor.execute(f"SELECT name FROM {table} LIMIT 5")
            names = [row[0] for row in cursor.fetchall()]
            print(f"  - Examples: {', '.join(names)}")
            
        except sqlite3.OperationalError as e:
            print(f"Table '{table}': Error - {e}")
            
    conn.close()

if __name__ == "__main__":
    verify()
