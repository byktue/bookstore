import sqlite3
from pymongo import MongoClient

# 配置路径和连接信息
SQLITE_DB_PATH = r"C:\Users\26930\Desktop\book_lx.db"  # 替换为你的SQLite数据库路径
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "bookstore"  # 目标MongoDB数据库名
MONGO_COLLECTION_NAME = "books"  # 目标集合名


# 读取SQLite数据（表名为book）
def read_sqlite_data():
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # 查询book表的所有字段
        cursor.execute("PRAGMA table_info(book);")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"book表的字段：{columns}")

        # 读取所有数据
        cursor.execute("SELECT * FROM book;")
        rows = cursor.fetchall()
        print(f"共读取 {len(rows)} 条数据")

        # 转换为字典列表
        data = []
        for row in rows:
            item = dict(zip(columns, row))
            # 补充MongoDB所需的store_id（若SQLite无此字段，可设为默认值）
            item["store_id"] = "default_store"  # 替换为实际店铺ID，若无则设默认
            item["book_id"] = item["id"]  # 映射SQLite的id到MongoDB的book_id
            data.append(item)
        return data

    except Exception as e:
        print(f"读取SQLite数据失败：{e}")
        return []
    finally:
        if conn:
            conn.close()


# 写入MongoDB
def write_to_mongodb(data):
    if not data:
        print("无数据可导入")
        return

    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]

        # 批量插入
        result = collection.insert_many(data)
        print(f"成功导入 {len(result.inserted_ids)} 条数据到MongoDB的{MONGO_COLLECTION_NAME}集合")

    except Exception as e:
        print(f"写入MongoDB失败：{e}")
    finally:
        client.close()


# 执行迁移
if __name__ == "__main__":
    print("开始从SQLite迁移数据到MongoDB...")
    sqlite_data = read_sqlite_data()
    if sqlite_data:
        write_to_mongodb(sqlite_data)
    print("迁移完成")