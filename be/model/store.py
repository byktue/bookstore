import logging
import threading
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure, DuplicateKeyError

class Store:
    db: Database

    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        try:
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000
            )
            self.client.admin.command('ping')  # 验证连接
            self.db = self.client['bookstore']
            self.clean_critical_invalid_data()  # 清理关键无效数据
            self.init_collections()
            logging.info("MongoDB 初始化成功")
        except Exception as e:
            logging.error(f"MongoDB 初始化失败: {str(e)}")
            raise

    def clean_critical_invalid_data(self):
        """清理会导致索引创建失败的关键无效数据"""
        try:
            # 删除 store_id 或 book_id 为空的记录
            null_count = self.db.books.delete_many({
                "$or": [
                    {"store_id": {"$in": [None, ""]}},
                    {"book_id": {"$in": [None, ""]}}
                ]
            }).deleted_count
            if null_count > 0:
                logging.warning(f"已删除 {null_count} 条 store_id/book_id 为空的无效记录")
            else:
                logging.info("未发现 store_id/book_id 为空的无效记录")

            # 检测重复记录（仅日志提示，不自动删除）
            duplicates = list(self.db.books.aggregate([
                {
                    "$group": {
                        "_id": {"store_id": "$store_id", "book_id": "$book_id"},
                        "count": {"$sum": 1},
                        "ids": {"$push": "$_id"}
                    }
                },
                {"$match": {"count": {"$gt": 1}}}
            ]))

            if duplicates:
                logging.warning(f"发现 {len(duplicates)} 组 (store_id, book_id) 重复记录，需手动处理")
            else:
                logging.info("未发现 (store_id, book_id) 重复记录")

        except Exception as e:
            logging.error(f"清理关键无效数据时出错: {str(e)}")
            raise

    def init_collections(self):
        # 用户相关索引
        self.db.user.create_index('user_id', unique=True, background=True)
        self.db.user_store.create_index(
            [('user_id', 1), ('store_id', 1)],
            unique=True,
            background=True
        )

        # 图书相关索引
        try:
            self.db.books.create_index(
                [('store_id', 1), ('book_id', 1)],
                unique=True,
                background=True
            )
            logging.info("books 集合 (store_id, book_id) 唯一索引创建成功")
        except DuplicateKeyError as e:
            logging.error(
                "\n===== 索引创建失败：存在重复的 (store_id, book_id) 记录 ====="
                "\n请手动处理重复记录后重试"
                "\n错误详情：%s", e
            )
            raise

        # 全文搜索索引
        try:
            self.db.books.create_index(
                [
                    ("title", "text"),
                    ("tags", "text"),
                    ("catalog", "text"),
                    ("content", "text")
                ],
                name="book_search_index",
                background=True,
                weights={
                    "title": 10,
                    "tags": 5,
                    "catalog": 3,
                    "content": 1
                }
            )
            logging.info("books 集合全文索引创建成功")
        except OperationFailure as e:
            if e.code == 85:
                logging.info("books 集合全文索引已存在")
            else:
                logging.error(f"全文索引创建失败: {str(e)}")
                raise

        # 订单相关索引
        self.db.new_order.create_index('order_id', unique=True, background=True)
        self.db.new_order_detail.create_index(
            [('order_id', 1), ('book_id', 1)],
            unique=True,
            background=True
        )

    def get_db(self) -> Database:
        """提供数据库连接实例"""
        return self.db

    def close(self):
        if hasattr(self, 'client'):
            self.client.close()
            logging.info("MongoDB 连接关闭")

# 全局实例管理
database_instance: Store = None
init_completed_event = threading.Event()

def init_database(mongo_uri: str = "mongodb://localhost:27017/"):
    """初始化数据库（供 serve.py 调用）"""
    global database_instance
    if database_instance is None:
        database_instance = Store(mongo_uri)
        init_completed_event.set()
    return database_instance

def get_db() -> Database:  # 改回 get_db
    """对外提供数据库连接的入口"""
    init_completed_event.wait()
    if database_instance is None:
        raise Exception("数据库未初始化")
    return database_instance.get_db()
def close_database():
    """关闭数据库连接"""
    global database_instance
    if database_instance:
        database_instance.close()
        database_instance = None
        init_completed_event.clear()