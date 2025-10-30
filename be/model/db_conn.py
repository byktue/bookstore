from be.model import store


class DBConn:
    """数据库连接及基础检查类"""
    def __init__(self):
        # 初始化数据库连接（从store模块获取）
        self.conn = store.get_db_conn()

    def user_id_exist(self, user_id):
        """检查用户ID是否存在于user表中"""
        cursor = self.conn.execute(
            "SELECT user_id FROM user WHERE user_id = ?;", (user_id,)
        )
        row = cursor.fetchone()
        return row is not None  # 存在返回True，否则返回False

    def book_id_exist(self, store_id, book_id):
        """检查指定店铺中是否存在该书籍ID"""
        cursor = self.conn.execute(
            "SELECT book_id FROM store WHERE store_id = ? AND book_id = ?;",
            (store_id, book_id),
        )
        row = cursor.fetchone()
        return row is not None  # 存在返回True，否则返回False

    def store_id_exist(self, store_id):
        """检查店铺ID是否存在于user_store表中"""
        cursor = self.conn.execute(
            "SELECT store_id FROM user_store WHERE store_id = ?;", (store_id,)
        )
        row = cursor.fetchone()
        return row is not None  # 存在返回True，否则返回False