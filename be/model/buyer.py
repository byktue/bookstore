import uuid
import json
import logging
from pymongo import MongoClient
from be.model import error
from be.model.user import User  # 导入用户类用于 Token 验证


class Buyer:
    def __init__(self):
        # 连接本地 MongoDB（默认端口 27017）
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['bookstore']  # 使用 bookstore 数据库

        # 初始化集合（对应原 SQL 表）
        self.store_col = self.db['store']  # 店铺库存集合
        self.order_col = self.db['new_order']  # 订单主集合
        self.order_detail_col = self.db['new_order_detail']  # 订单详情集合
        self.user_col = self.db['user']  # 用户集合
        self.user_store_col = self.db['user_store']  # 用户-店铺关联集合

        # 初始化 User 实例用于 Token 验证
        self.user = User()

    # 辅助方法：检查用户是否存在
    def user_id_exist(self, user_id: str) -> bool:
        return self.user_col.find_one({'user_id': user_id}) is not None

    # 辅助方法：检查店铺是否存在
    def store_id_exist(self, store_id: str) -> bool:
        return self.user_store_col.find_one({'store_id': store_id}) is not None

    def new_order(
            self, user_id: str, store_id: str, id_and_count: [(str, int)]
    ) -> (int, str, str):
        order_id = ""
        try:
            # 验证用户存在性
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)

            # 验证店铺存在性
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            # 生成唯一订单 ID
            order_id = f"{user_id}_{store_id}_{uuid.uuid1().hex}"

            # 检查并扣减库存，同时准备订单详情
            order_details = []
            for book_id, count in id_and_count:
                # 查询图书库存
                book = self.store_col.find_one({
                    'store_id': store_id,
                    'book_id': book_id
                })
                if not book:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                # 检查库存是否充足
                if book['stock_level'] < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 扣减库存（原子操作，避免并发问题）
                result = self.store_col.update_one(
                    {
                        'store_id': store_id,
                        'book_id': book_id,
                        'stock_level': {'$gte': count}  # 确保扣减前库存充足
                    },
                    {'$inc': {'stock_level': -count}}
                )
                if result.modified_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 准备订单详情
                book_info = json.loads(book['book_info'])
                order_details.append({
                    'order_id': order_id,
                    'book_id': book_id,
                    'count': count,
                    'price': book_info.get('price', 0)
                })

            # 插入订单详情
            if order_details:
                self.order_detail_col.insert_many(order_details)

            # 插入订单主记录（状态初始为 'unpaid'）
            self.order_col.insert_one({
                'order_id': order_id,
                'store_id': store_id,
                'user_id': user_id,
                'status': 'unpaid'
            })

            return 200, "ok", order_id

        except Exception as e:
            logging.error(f"530, {str(e)}")
            return 530, f"{str(e)}", ""

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查询订单
            order = self.order_col.find_one({'order_id': order_id})
            if not order:
                return error.error_invalid_order_id(order_id)

            # 验证订单状态为未付款
            if order['status'] != 'unpaid':
                return error.error_invalid_order_status(order_id, 'unpaid')

            # 验证订单归属
            buyer_id = order['user_id']
            if buyer_id != user_id:
                return error.error_authorization_fail()

            # 验证买家密码
            buyer = self.user_col.find_one({'user_id': buyer_id})
            if not buyer:
                return error.error_non_exist_user_id(buyer_id)
            if buyer['password'] != password:
                return error.error_authorization_fail()

            # 查询店铺对应的卖家
            store = self.user_store_col.find_one({'store_id': order['store_id']})
            if not store:
                return error.error_non_exist_store_id(order['store_id'])
            seller_id = store['user_id']

            # 验证卖家存在
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            # 计算订单总金额
            details = self.order_detail_col.find({'order_id': order_id})
            total_price = sum(d['count'] * d['price'] for d in details)

            # 验证买家余额充足
            if buyer['balance'] < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣减买家余额（原子操作）
            buyer_update = self.user_col.update_one(
                {
                    'user_id': buyer_id,
                    'balance': {'$gte': total_price}  # 确保扣减前余额充足
                },
                {'$inc': {'balance': -total_price}}
            )
            if buyer_update.modified_count == 0:
                return error.error_not_sufficient_funds(order_id)

            # 增加卖家余额
            self.user_col.update_one(
                {'user_id': seller_id},
                {'$inc': {'balance': total_price}}
            )

            # 更新订单状态为已付款
            self.order_col.update_one(
                {'order_id': order_id},
                {'$set': {'status': 'paid'}}
            )

            return 200, "ok"

        except Exception as e:
            logging.error(f"530, {str(e)}")
            return 530, f"{str(e)}"

    def add_funds(self, user_id: str, password: str, add_value: int) -> (int, str):
        try:
            # 验证用户存在且密码正确
            user = self.user_col.find_one({
                'user_id': user_id,
                'password': password
            })
            if not user:
                return error.error_authorization_fail()

            # 增加余额
            self.user_col.update_one(
                {'user_id': user_id},
                {'$inc': {'balance': add_value}}
            )

            return 200, "ok"

        except Exception as e:
            logging.error(f"530, {str(e)}")
            return 530, f"{str(e)}"

    def receive_order(self, user_id: str, order_id: str, token: str) -> (int, str):
        try:
            # 验证 Token 有效性
            if not self.user.check_token(token, user_id):
                return error.error_authorization_fail()

            # 查询订单
            order = self.order_col.find_one({'order_id': order_id})
            if not order:
                return error.error_invalid_order_id(order_id)

            # 验证订单归属
            if order['user_id'] != user_id:
                return error.error_authorization_fail()

            # 验证订单状态为已发货
            if order['status'] != 'shipped':
                return error.error_order_not_shipped(order_id)

            # 更新订单状态为已收货
            self.order_col.update_one(
                {'order_id': order_id},
                {'$set': {'status': 'received'}}
            )

            return 200, "ok"

        except Exception as e:
            logging.error(f"530, {str(e)}")
            return 530, f"{str(e)}"