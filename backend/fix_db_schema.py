import sqlite3
import os

# Define the path to the database
# Based on config.py logic: d:\Tiga\backend\recorder_v5.db
db_path = os.path.join("d:\\Tiga\\backend", "recorder_v5.db")

print(f"Connecting to database at: {db_path}")

if not os.path.exists(db_path):
    print("Database file not found!")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists first
    cursor.execute("PRAGMA table_info(nodes)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "group" in columns:
        print("Column 'group' already exists in table 'nodes'.")
    else:
        print("Adding column 'group' to table 'nodes'...")
        # "group" is a reserved keyword in SQL, so we quote it
        cursor.execute('ALTER TABLE nodes ADD COLUMN "group" TEXT')
        conn.commit()
        print("Successfully added column 'group'.")
        
    conn.close()

except Exception as e:
    print(f"An error occurred: {e}")
