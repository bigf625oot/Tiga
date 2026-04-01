from neo4j import GraphDatabase
import sys

def test_neo4j_connection():
    # 配置信息
    host = "8.130.137.244"
    port = 33071
    user = "neo4j"
    password = "password"
    database = "tiga_case"
    
    # 构造连接 URI (bolt 协议)
    uri = f"bolt://{host}:{port}"

    print(f"正在尝试连接到 {uri} (数据库: {database})...")

    driver = None
    try:
        # 初始化驱动程序
        driver = GraphDatabase.driver(
            uri, 
            auth=(user, password), 
            encrypted=True # 用户截图开启了SSL
        )

        # 验证连接并执行简单查询
        with driver.session(database=database) as session:
            # 执行一个简单的 Cypher 查询
            result = session.run("RETURN '连接成功！' AS message, datetime() AS current_time")
            record = result.single()
            
            if record:
                print("-" * 30)
                print(f"状态: {record['message']}")
                print(f"服务器时间: {record['current_time']}")
                print("-" * 30)

    except Exception as e:
        print(f"\n[错误] 无法连接到 Neo4j:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.close()
            print("连接已关闭。")

if __name__ == "__main__":
    test_neo4j_connection()