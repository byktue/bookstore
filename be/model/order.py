from be.model import error
from be.model.store import get_db
import uuid
import time
import traceback


class Order:
    # 订单状态常量
    STATUS_UNPAID = 1       # 未付款
    STATUS_CANCELED = 0     # 已取消
    STATUS_TIMEOUT = -1     # 超时取消
    STATUS_PAID = 2         # 已付款
    STATUS_SHIPPED = 3      # 已发货
    STATUS_RECEIVED = 4     # 已收货

    def __init__(self):
        self.db = get_db()
        # 数据库集合（与store.py保持一致）
        self.user_store_col = self.db['user_store']  # 店铺归属
        self.store_col = self.db['store']            # 图书库存
        self.order_col = self.db['new_order']        # 订单集合
        self.user_col = self.db['user']              # 用户集合

    def store_id_exist(self, store_id: str) -> bool:
        """检查店铺是否存在"""
        return self.user_store_col.find_one({'store_id': store_id}) is not None

    def create_order(
        self,
        user_id: str,
        store_id: str,
        book_ids: list,
        quantities: list
    ) -> (int, str, str):
        try:
            # 1. 验证店铺存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + ("",)

            # 2. 验证用户存在
            if self.user_col.find_one({'user_id': user_id}) is None:
                return error.error_non_exist_user_id(user_id) + ("",)

            # 3. 验证图书ID与数量长度匹配
            if len(book_ids) != len(quantities):
                return error.error_invalid_parameter("book_ids与quantities长度不匹配") + ("",)

            # 4. 验证图书存在且库存充足
            total_price = 0
            order_books = []
            for book_id, quantity in zip(book_ids, quantities):
                # 查询图书（关联店铺和库存）
                book = self.store_col.find_one({
                    'store_id': store_id,
                    'book_id': book_id
                })
                if not book:
                    return error.error_non_exist_book_id(book_id) + ("",)
                # 检查库存（字段名为stock_level）
                if book.get('stock_level', 0) < quantity:
                    return error.error_stock_level_low(book_id) + ("",)

                # 计算总价
                total_price += book['price'] * quantity
                order_books.append({
                    'book_id': book_id,
                    'quantity': quantity,
                    'price': book['price']
                })

            # 5. 创建订单记录
            order_id = f"order_{uuid.uuid1().hex[:16]}"
            self.order_col.insert_one({
                'order_id': order_id,
                'user_id': user_id,
                'store_id': store_id,
                'books': order_books,
                'total_price': total_price,
                'status': self.STATUS_UNPAID,
                'create_time': time.time()
            })

            # 6. 扣减库存
            for book_id, quantity in zip(book_ids, quantities):
                self.store_col.update_one(
                    {'store_id': store_id, 'book_id': book_id},
                    {'$inc': {'stock_level': -quantity}}
                )

            return 200, "ok", order_id

        except Exception as e:
            err_msg = f"创建订单失败：{str(e)}\n{traceback.format_exc()}"
            return 530, err_msg, ""

    def get_user_orders(self, user_id: str) -> (int, str, list):
        try:
            if self.user_col.find_one({'user_id': user_id}) is None:
                return error.error_non_exist_user_id(user_id) + ([],)

            orders = list(self.order_col.find({'user_id': user_id}))
            # 转换ObjectId为字符串（避免JSON序列化错误）
            order_list = []
            for order in orders:
                order['_id'] = str(order['_id'])
                order_list.append(order)
            return 200, "ok", order_list
        except Exception as e:
            err_msg = f"查询订单失败：{str(e)}\n{traceback.format_exc()}"
            return 530, err_msg, []

    def cancel_order(self, user_id: str, order_id: str) -> (int, str):
        try:
            order = self.order_col.find_one({
                'order_id': order_id,
                'user_id': user_id
            })
            if not order:
                return error.error_invalid_order_id(order_id)

            # 只有未付款订单可取消
            if order['status'] != self.STATUS_UNPAID:
                return error.error_invalid_order_status(order_id, f"未付款（{self.STATUS_UNPAID}）")

            # 恢复库存
            store_id = order['store_id']
            for book in order['books']:
                self.store_col.update_one(
                    {'store_id': store_id, 'book_id': book['book_id']},
                    {'$inc': {'stock_level': book['quantity']}}
                )

            # 更新订单状态为已取消
            self.order_col.update_one(
                {'order_id': order_id},
                {'$set': {'status': self.STATUS_CANCELED}}
            )
            return 200, "ok"
        except Exception as e:
            err_msg = f"取消订单失败：{str(e)}\n{traceback.format_exc()}"
            return 530, err_msg

    def check_timeout_orders(self) -> (int, str):
        try:
            timeout_seconds = 30 * 60  # 30分钟超时
            current_time = time.time()
            # 查询所有未付款且超时的订单
            timeout_orders = self.order_col.find({
                'status': self.STATUS_UNPAID,
                'create_time': {'$lt': current_time - timeout_seconds}
            })

            count = 0
            for order in timeout_orders:
                # 恢复库存
                store_id = order['store_id']
                for book in order['books']:
                    self.store_col.update_one(
                        {'store_id': store_id, 'book_id': book['book_id']},
                        {'$inc': {'stock_level': book['quantity']}}
                    )
                # 更新订单状态为“超时取消”
                self.order_col.update_one(
                    {'order_id': order['order_id']},
                    {'$set': {'status': self.STATUS_TIMEOUT}}
                )
                count += 1

            return count, f"处理了 {count} 个超时未付款订单"
        except Exception as e:
            err_msg = f"检查超时订单失败：{str(e)}\n{traceback.format_exc()}"
            return 0, err_msg