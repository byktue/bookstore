from pymongo import MongoClient
from be.model import error
from be.model.user import User  # 导入用户类用于 Token 验证


class Seller:
    def __init__(self):
        # 连接本地 MongoDB（默认端口 27017）
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['bookstore']  # 使用 bookstore 数据库

        # 初始化集合（对应原 SQL 表）
        self.store_col = self.db['store']  # 店铺库存集合
        self.user_store_col = self.db['user_store']  # 用户-店铺关联集合
        self.order_col = self.db['new_order']  # 订单集合
        self.user_col = self.db['user']  # 用户集合

        # 初始化 User 实例用于 Token 验证
        self.user = User()

    # 辅助方法：检查用户是否存在
    def user_id_exist(self, user_id: str) -> bool:
        return self.user_col.find_one({'user_id': user_id}) is not None

    # 辅助方法：检查店铺是否存在
    def store_id_exist(self, store_id: str) -> bool:
        return self.user_store_col.find_one({'store_id': store_id}) is not None

    # 辅助方法：检查图书是否存在于店铺
    def book_id_exist(self, store_id: str, book_id: str) -> bool:
        return self.store_col.find_one({
            'store_id': store_id,
            'book_id': book_id
        }) is not None

    def add_book(
            self,
            user_id: str,
            store_id: str,
            book_id: str,
            book_json_str: str,
            stock_level: int,
    ) -> (int, str):
        try:
            # 验证用户存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            # 验证店铺存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            # 验证图书不存在于店铺
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # 插入图书到店铺库存
            self.store_col.insert_one({
                'store_id': store_id,
                'book_id': book_id,
                'book_info': book_json_str,  # 保留原 JSON 字符串格式
                'stock_level': stock_level
            })

            return 200, "ok"

        except Exception as e:
            return 530, f"系统错误：{str(e)}"

    def add_stock_level(
            self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ) -> (int, str):
        try:
            # 验证用户存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            # 验证店铺存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            # 验证图书存在于店铺
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # 增加库存（原子操作）
            self.store_col.update_one(
                {
                    'store_id': store_id,
                    'book_id': book_id
                },
                {'$inc': {'stock_level': add_stock_level}}  # 累加库存
            )

            return 200, "ok"

        except Exception as e:
            return 530, f"系统错误：{str(e)}"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            # 验证用户存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            # 验证店铺不存在
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            # 创建店铺（关联用户-店铺）
            self.user_store_col.insert_one({
                'store_id': store_id,
                'user_id': user_id
            })

            return 200, "ok"

        except Exception as e:
            return 530, f"系统错误：{str(e)}"

    def ship_order(self, seller_id: str, store_id: str, order_id: str, token: str) -> (int, str):
        try:
            # 1. 验证 Token 有效性
            if not self.user.check_token(token, seller_id):
                return error.error_authorization_fail()

            # 2. 验证店铺存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            # 3. 验证卖家是否为店铺所有者
            if not self._is_store_owner(seller_id, store_id):
                return error.error_authorization_fail()

            # 4. 查询订单并验证存在性
            order = self.get_order(order_id)
            if not order:
                return error.error_invalid_order_id(order_id)

            # 5. 验证订单状态为已付款
            if order['status'] != "paid":
                return error.error_order_not_paid(order_id)

            # 6. 验证订单归属当前店铺
            if order['store_id'] != store_id:
                return error.error_authorization_fail()

            # 7. 更新订单状态为已发货
            self.update_order_status(order_id, "shipped")

            return 200, "ok"

        except Exception as e:
            return 530, f"系统错误：{str(e)}"

    def get_order(self, order_id: str) -> dict:
        """查询订单信息（返回字典格式，适配 MongoDB）"""
        return self.order_col.find_one({
            'order_id': order_id
        })

    def update_order_status(self, order_id: str, status: str) -> None:
        """更新订单状态（原子操作）"""
        self.order_col.update_one(
            {'order_id': order_id},
            {'$set': {'status': status}}
        )

    def _is_store_owner(self, user_id: str, store_id: str) -> bool:
        """验证用户是否为店铺所有者"""
        return self.user_store_col.find_one({
            'user_id': user_id,
            'store_id': store_id
        }) is not None