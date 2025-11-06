from be.model import store  # 假设 store 中已实现 MongoDB 连接逻辑

class DBConn:
    def __init__(self):
        # 获取 MongoDB 数据库连接（复用 store 中的初始化逻辑）
        self.db = store.get_db_conn()  # 假设返回的是 pymongo.database.Database 对象

    def user_id_exist(self, user_id: str) -> bool:
        """检查用户ID是否存在"""
        # 查询 user 集合中是否有匹配的 user_id
        count = self.db["user"].count_documents({"user_id": user_id})
        return count > 0

    def book_id_exist(self, store_id: str, book_id: str) -> bool:
        """检查店铺中是否存在指定图书ID"""
        # 查询 store 集合中是否有匹配的 store_id 和 book_id
        count = self.db["store"].count_documents({
            "store_id": store_id,
            "book_id": book_id
        })
        return count > 0

    def store_id_exist(self, store_id: str) -> bool:
        """检查店铺ID是否存在"""
        # 查询 user_store 集合中是否有匹配的 store_id
        count = self.db["user_store"].count_documents({"store_id": store_id})
        return count > 0