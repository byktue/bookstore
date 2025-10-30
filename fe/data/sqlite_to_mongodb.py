import sqlite3
from pymongo import MongoClient
from bson import Binary
import os

def migrate_sqlite_to_mongodb(sqlite_db_path, mongo_uri, mongo_db_name, mongo_collection_name):
    # 1. 连接 SQLite 数据库
    try:
        sqlite_conn = sqlite3.connect(sqlite_db_path)
    except sqlite3.OperationalError as e:
        print(f"无法连接 SQLite 数据库：{e}")
        print(f"检查路径是否正确：{sqlite_db_path}")
        return
    sqlite_cursor = sqlite_conn.cursor()

    # 2. 连接 MongoDB
    try:
        mongo_client = MongoClient(mongo_uri)
        # 验证 MongoDB 连接
        mongo_client.admin.command('ping')
    except Exception as e:
        print(f"无法连接 MongoDB：{e}")
        sqlite_conn.close()
        return
    mongo_db = mongo_client[mongo_db_name]
    collection = mongo_db[mongo_collection_name]

    # 3. 读取 SQLite 中的 book 表数据
    try:
        sqlite_cursor.execute("SELECT * FROM book")
    except sqlite3.OperationalError as e:
        print(f"SQLite 表操作错误：{e}")
        sqlite_conn.close()
        mongo_client.close()
        return
    columns = [desc[0] for desc in sqlite_cursor.description]

    # 4. 转换并插入 MongoDB
    count = 0
    for row in sqlite_cursor.fetchall():
        book_data = dict(zip(columns, row))
        
        # 处理 BLOB 类型
        if book_data.get("picture") is not None:
            book_data["picture"] = Binary(book_data["picture"])
        
        # 处理 tags 数组
        if book_data.get("tags"):
            book_data["tags"] = [tag.strip() for tag in book_data["tags"].split("\n") if tag.strip()]
        
        # 插入或更新
        collection.replace_one(
            {"_id": book_data["id"]},
            book_data,
            upsert=True
        )
        count += 1
        if count % 100 == 0:
            print(f"已迁移 {count} 条数据")

    print(f"迁移完成，共处理 {count} 条数据")

    # 关闭连接
    sqlite_conn.close()
    mongo_client.close()

if __name__ == "__main__":
    # 动态计算 SQLite 数据库路径（关键修正）
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接数据库路径（根据项目结构：fe/data/book.db）
    SQLITE_DB_PATH = os.path.join(current_dir, "..", "..", "fe", "data", "book_lx.db")
    # 规范化路径（处理 .. 等相对路径）
    SQLITE_DB_PATH = os.path.normpath(SQLITE_DB_PATH)

    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB_NAME = "bookstore"
    MONGO_COLLECTION_NAME = "books"

    migrate_sqlite_to_mongodb(SQLITE_DB_PATH, MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME)