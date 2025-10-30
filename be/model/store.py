import logging
import os
import sqlite3 as sqlite
import threading


class Store:
    database: str  # 数据库文件路径（类属性）

    def __init__(self, db_path):
        # 初始化：拼接数据库文件完整路径（db_path目录下的be.db）
        self.database = os.path.join(db_path, "be.db")
        # 初始化数据库表结构
        self.init_tables()

    def init_tables(self):
        """创建数据库所需表（若表不存在），包含用户、店铺、书籍、订单相关表"""
        try:
            # 获取数据库连接
            conn = self.get_db_conn()
            # 1. 用户表：存储用户ID、密码、余额、token、终端信息
            conn.execute(
                "CREATE TABLE IF NOT EXISTS user ("
                "user_id TEXT PRIMARY KEY, password TEXT NOT NULL, "
                "balance INTEGER NOT NULL, token TEXT, terminal TEXT);"
            )

            # 2. 用户-店铺关联表：记录用户与店铺的归属关系（联合主键防重复）
            conn.execute(
                "CREATE TABLE IF NOT EXISTS user_store("
                "user_id TEXT, store_id, PRIMARY KEY(user_id, store_id));"
            )

            # 3. 店铺书籍表：存储店铺内书籍信息（店铺ID+书籍ID联合主键防重复）
            conn.execute(
                "CREATE TABLE IF NOT EXISTS store( "
                "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER,"
                " PRIMARY KEY(store_id, book_id))"
            )

            # 4. 订单表：存储订单基本信息（订单ID为主键）
            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order( "
                "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT)"
            )

            # 5. 订单详情表：存储订单内书籍明细（订单ID+书籍ID联合主键防重复）
            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order_detail( "
                "order_id TEXT, book_id TEXT, count INTEGER, price INTEGER,  "
                "PRIMARY KEY(order_id, book_id))"
            )

            # 提交表创建操作
            conn.commit()
        except sqlite.Error as e:
            # 捕获SQLite错误并记录日志，回滚操作
            logging.error(e)
            conn.rollback()

    def get_db_conn(self) -> sqlite.Connection:
        """获取SQLite数据库连接（返回连接对象供后续操作）"""
        return sqlite.connect(self.database)


# 全局数据库实例（单例模式，供整个系统调用）
database_instance: Store = None
# 数据库初始化完成事件（用于线程同步，确保初始化完成后再使用）
init_completed_event = threading.Event()


def init_database(db_path):
    """初始化数据库：创建Store实例并赋值给全局变量，标记初始化完成"""
    global database_instance
    database_instance = Store(db_path)


def get_db_conn():
    """对外提供数据库连接：通过全局Store实例获取连接"""
    global database_instance
    return database_instance.get_db_conn()