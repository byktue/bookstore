from be.model import error
from be.model.user import User
from be.model.store import get_db  # 使用统一数据库连接
import json
import traceback
import time


class Seller:
    def __init__(self):
        self.db = get_db()  # 统一数据库连接
        # 集合与store.py初始化的保持一致
        self.books_col = self.db['books']
        self.user_store_col = self.db['user_store']  # 店铺归属集合（与store.py一致）
        self.order_col = self.db['new_order']
        self.user_col = self.db['user']
        self.user = User()

    # 验证用户存在
    def user_id_exist(self, user_id: str) -> bool:
        return self.user_col.find_one({'user_id': user_id}) is not None

    # 验证店铺存在（与订单模块逻辑完全一致）
    def store_id_exist(self, store_id: str) -> bool:
        return self.user_store_col.find_one({'store_id': store_id}) is not None

    # 验证图书存在于店铺
    def book_id_exist(self, store_id: str, book_id: str) -> bool:
        return self.books_col.find_one({
            'store_id': store_id,
            'book_id': book_id
        }) is not None

    # 创建店铺（确保写入user_store集合）
    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            # 插入店铺记录到user_store集合（与store.py的索引匹配）
            result = self.user_store_col.insert_one({
                'user_id': user_id,
                'store_id': store_id,
                'create_time': time.time()
            })
            if not result.acknowledged:
                return 530, "店铺创建失败：数据库写入未确认"

            return 200, "ok"
        except Exception as e:
            traceback.print_exc()
            return 530, f"系统错误：{str(e)}"

    # 添加图书（保持不变）
    def add_book(
            self,
            user_id: str,
            store_id: str,
            book_id: str,
            book_json_str: str,
            stock_level: int,
    ) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            try:
                book_info = json.loads(book_json_str)
            except json.JSONDecodeError as e:
                return 400, f"图书信息解析失败：{str(e)}"

            self.books_col.insert_one({
                'store_id': store_id,
                'book_id': book_id,
                'stock': stock_level,
                'price': book_info.get('price', 0),
                'title': book_info.get('title', ''),
                'book_info': book_json_str
            })
            return 200, "ok"
        except Exception as e:
            traceback.print_exc()
            return 530, f"系统错误：{str(e)}"

    # 其他方法（add_stock_level/ship_order等保持不变）
    def add_stock_level(
            self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            self.books_col.update_one(
                {'store_id': store_id, 'book_id': book_id},
                {'$inc': {'stock': add_stock_level}}
            )
            return 200, "ok"
        except Exception as e:
            traceback.print_exc()
            return 530, f"系统错误：{str(e)}"

    def ship_order(self, seller_id: str, store_id: str, order_id: str, token: str) -> (int, str):
        try:
            if not self.user.check_token(token, seller_id):
                return error.error_authorization_fail()
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self._is_store_owner(seller_id, store_id):
                return error.error_authorization_fail()

            order = self.order_col.find_one({'order_id': order_id})
            if not order:
                return error.error_invalid_order_id(order_id)
            if order['status'] != 2:  # 2: 已付款
                return error.error_order_not_paid(order_id)
            if order['store_id'] != store_id:
                return error.error_authorization_fail()

            self.order_col.update_one(
                {'order_id': order_id},
                {'$set': {'status': 3}}  # 3: 已发货
            )
            return 200, "ok"
        except Exception as e:
            traceback.print_exc()
            return 530, f"系统错误：{str(e)}"

    def _is_store_owner(self, user_id: str, store_id: str) -> bool:
        return self.user_store_col.find_one({
            'user_id': user_id,
            'store_id': store_id
        }) is not None