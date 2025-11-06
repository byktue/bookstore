from be.model import error
from be.model.store import get_db  # 使用store.py提供的统一数据库连接
import uuid
import time


class Order:
    def __init__(self):
        self.db = get_db()  # 关键：使用全局统一的数据库连接
        # 订单模块依赖的集合（与store.py初始化的集合一致）
        self.user_store_col = self.db['user_store']  # 店铺归属集合
        self.books_col = self.db['books']           # 图书库存集合
        self.order_col = self.db['new_order']       # 订单集合
        self.user_col = self.db['user']             # 用户集合

    # 验证店铺存在（与卖家模块逻辑一致）
    def store_id_exist(self, store_id: str) -> bool:
        """检查店铺是否存在于user_store集合（与seller.py完全一致）"""
        return self.user_store_col.find_one({'store_id': store_id}) is not None

    # 创建订单（核心修复：先验证店铺存在）
    def create_order(
        self,
        user_id: str,
        store_id: str,
        book_ids: list,
        quantities: list
    ) -> (int, str, str):
        try:
            # 1. 优先验证店铺存在（解决核心错误）
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            # 2. 验证用户存在
            if self.user_col.find_one({'user_id': user_id}) is None:
                return error.error_non_exist_user_id(user_id)

            # 3. 验证图书ID与数量长度匹配
            if len(book_ids) != len(quantities):
                return error.error_invalid_parameter("book_ids与quantities长度不匹配")

            # 4. 验证图书存在且库存充足
            total_price = 0
            order_books = []
            for book_id, quantity in zip(book_ids, quantities):
                # 查询图书（关联店铺）
                book = self.books_col.find_one({
                    'store_id': store_id,
                    'book_id': book_id
                })
                if not book:
                    return error.error_non_exist_book_id(book_id)
                if book.get('stock', 0) < quantity:
                    return error.error_low_stock(book_id)

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
                'status': 1,  # 1: 未付款
                'create_time': time.time()
            })

            # 6. 扣减库存
            for book_id, quantity in zip(book_ids, quantities):
                self.books_col.update_one(
                    {'store_id': store_id, 'book_id': book_id},
                    {'$inc': {'stock': -quantity}}
                )

            return 200, "ok", order_id

        except Exception as e:
            return 530, f"创建订单失败：{str(e)}", ""

    # 查询用户订单
    def get_user_orders(self, user_id: str) -> (int, str, list):
        try:
            if self.user_col.find_one({'user_id': user_id}) is None:
                return error.error_non_exist_user_id(user_id)

            orders = list(self.order_col.find({'user_id': user_id}))
            # 转换ObjectId为字符串（避免JSON序列化错误）
            order_list = []
            for order in orders:
                order['_id'] = str(order['_id'])
                order_list.append(order)
            return 200, "ok", order_list
        except Exception as e:
            return 530, f"查询订单失败：{str(e)}", []

    # 取消订单
    def cancel_order(self, user_id: str, order_id: str) -> (int, str):
        try:
            order = self.order_col.find_one({
                'order_id': order_id,
                'user_id': user_id
            })
            if not order:
                return error.error_invalid_order_id(order_id)

            # 只有未付款订单可取消
            if order['status'] != 1:
                return error.error_order_status_invalid(order_id)

            # 恢复库存
            store_id = order['store_id']
            for book in order['books']:
                self.books_col.update_one(
                    {'store_id': store_id, 'book_id': book['book_id']},
                    {'$inc': {'stock': book['quantity']}}
                )

            # 更新订单状态为已取消
            self.order_col.update_one(
                {'order_id': order_id},
                {'$set': {'status': 0}}
            )
            return 200, "ok"
        except Exception as e:
            return 530, f"取消订单失败：{str(e)}"

    def check_timeout_orders(self) -> (int, str):
        """检查并处理超时未付款的订单（默认30分钟超时）"""
        try:
            timeout_seconds = 30 * 60  # 30分钟超时
            current_time = time.time()
            # 查询所有未付款且超时的订单
            timeout_orders = self.order_col.find({
                'status': 1,  # 1: 未付款状态
                'create_time': {'$lt': current_time - timeout_seconds}
            })

            count = 0
            for order in timeout_orders:
                # 恢复库存
                store_id = order['store_id']
                for book in order['books']:
                    self.books_col.update_one(
                        {'store_id': store_id, 'book_id': book['book_id']},
                        {'$inc': {'stock': book['quantity']}}
                    )
                # 更新订单状态为“已取消（超时）”
                self.order_col.update_one(
                    {'order_id': order['order_id']},
                    {'$set': {'status': -1}}  # -1: 超时取消
                )
                count += 1

            return count, f"处理了 {count} 个超时未付款订单"
        except Exception as e:
            return 0, f"检查超时订单失败：{str(e)}"