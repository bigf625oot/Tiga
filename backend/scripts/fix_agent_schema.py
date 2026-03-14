import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recorder_v5.db")

def add_column_if_not_exists(cursor, table_name, column_name, column_type, default_value):
    print(f"Checking for column '{column_name}' in table '{table_name}'...")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    
    if column_name not in columns:
        print(f"Adding column '{column_name}' to table '{table_name}'...")
        try:
            # SQLite supports ADD COLUMN
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
            print(f"Column '{column_name}' added successfully.")
        except sqlite3.OperationalError as e:
            print(f"Error adding column '{column_name}': {e}")
    else:
        print(f"Column '{column_name}' already exists.")

def main():
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return

    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add enable_react column
        add_column_if_not_exists(cursor, "agents", "enable_react", "BOOLEAN", 1)
        
        # Add enable_cot column
        add_column_if_not_exists(cursor, "agents", "enable_cot", "BOOLEAN", 1)
        
        conn.commit()
        print("Database schema updated successfully.")
    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
