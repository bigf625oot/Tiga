import pymysql
import random
import string
import time
from datetime import datetime, timedelta

# DB Config
HOST = 'yyds123drt.mysql.rds.aliyuncs.com'
PORT = 3306
USER = 'Tang_2026'
PASS = 'SYsz8888@'
DB_NAME = 'test_db'

def get_connection(db=None):
    return pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASS,
        database=db,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def create_database():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            print(f"Creating database '{DB_NAME}' if not exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.commit()
    finally:
        conn.close()

def create_tables():
    conn = get_connection(DB_NAME)
    try:
        with conn.cursor() as cursor:
            # Drop tables to ensure clean slate with new schema
            print("Dropping existing tables to apply new schema...")
            cursor.execute("DROP TABLE IF EXISTS orders")
            cursor.execute("DROP TABLE IF EXISTS users")

            print("Creating table 'users' with company field...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    company VARCHAR(50) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            print("Creating table 'orders'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    order_number VARCHAR(20) NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    status ENUM('pending', 'paid', 'shipped', 'cancelled') DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
    finally:
        conn.close()

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_chinese_name():
    family_names = [
        "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈", 
        "褚", "卫", "蒋", "沈", "韩", "杨", "朱", "秦", "尤", "许",
        "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏", 
        "陶", "姜", "戚", "谢", "邹", "喻", "柏", "水", "窦", "章"
    ]
    given_names = [
        "伟", "芳", "娜", "敏", "静", "秀", "英", "娟", "艳", "强", 
        "军", "磊", "洋", "勇", "杰", "涛", "明", "超", "秀兰", "霞", 
        "平", "刚", "桂英", "志强", "建国", "建军", "婷婷", "玉兰", "海燕"
    ]
    return random.choice(family_names) + random.choice(given_names)

def mock_data():
    conn = get_connection(DB_NAME)
    try:
        with conn.cursor() as cursor:
            # Mock Users
            print("Generating 100 users with Chinese names and companies...")
            user_values = []
            companies = ['中电金信', '数势科技']
            
            for _ in range(100):
                username = generate_chinese_name()
                # Ensure simple email based on random string to avoid encoding issues in email
                email = f"user_{generate_random_string(6)}@example.com"
                company = random.choice(companies)
                user_values.append((username, email, company))
            
            cursor.executemany(
                "INSERT INTO users (username, email, company) VALUES (%s, %s, %s)",
                user_values
            )
            
            # Get User IDs to link orders
            cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 100")
            user_ids = [row['id'] for row in cursor.fetchall()]
            
            if not user_ids:
                # Fallback if fetch fails or table was empty before
                cursor.execute("SELECT id FROM users LIMIT 100")
                user_ids = [row['id'] for row in cursor.fetchall()]

            # Mock Orders
            print("Generating 100 orders...")
            order_values = []
            statuses = ['pending', 'paid', 'shipped', 'cancelled']
            for _ in range(100):
                user_id = random.choice(user_ids) if user_ids else 1
                order_number = f"ORD-{generate_random_string(6).upper()}"
                amount = round(random.uniform(10.0, 1000.0), 2)
                status = random.choice(statuses)
                order_values.append((user_id, order_number, amount, status))
            
            cursor.executemany(
                "INSERT INTO orders (user_id, order_number, amount, status) VALUES (%s, %s, %s, %s)",
                order_values
            )
            
        conn.commit()
        print("Mock data insertion completed.")
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        create_database()
        create_tables()
        mock_data()
    except Exception as e:
        print(f"An error occurred: {e}")
