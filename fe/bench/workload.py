import logging
import uuid
import random
import threading
from fe.access import book
from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access.buyer import Buyer
from fe import conf


class NewOrder:
    """创建订单的操作封装类，用于基准测试中的下单流程"""
    def __init__(self, buyer: Buyer, store_id, book_id_and_count):
        self.buyer = buyer  # 买家对象
        self.store_id = store_id  # 店铺ID
        self.book_id_and_count = book_id_and_count  # 书籍ID与购买数量的列表

    def run(self) -> (bool, str):
        """执行创建订单操作，返回操作结果和订单ID"""
        # 调用买家接口创建订单
        code, order_id = self.buyer.new_order(self.store_id, self.book_id_and_count)
        # 返回是否成功（状态码200为成功）和订单ID
        return code == 200, order_id


class Payment:
    """支付订单的操作封装类，用于基准测试中的支付流程"""
    def __init__(self, buyer: Buyer, order_id):
        self.buyer = buyer  # 买家对象
        self.order_id = order_id  # 订单ID

    def run(self) -> bool:
        """执行支付操作，返回是否成功"""
        code = self.buyer.payment(self.order_id)
        return code == 200  # 状态码200表示支付成功


class Workload:
    """基准测试的工作负载管理类，负责初始化测试数据、生成测试任务和统计性能指标"""
    def __init__(self):
        self.uuid = str(uuid.uuid1())  # 唯一标识本次测试，避免数据冲突
        self.book_ids = {}  # 存储店铺ID到书籍ID列表的映射
        self.buyer_ids = []  # 买家ID列表
        self.store_ids = []  # 店铺ID列表
        self.book_db = book.BookDB(conf.Use_Large_DB)  # 书籍数据库
        self.row_count = self.book_db.get_book_count()  # 书籍总数

        # 从配置文件加载测试参数
        self.book_num_per_store = conf.Book_Num_Per_Store
        if self.row_count < self.book_num_per_store:
            self.book_num_per_store = self.row_count  # 单个店铺的书籍数量（不超过总书籍数）
        self.store_num_per_user = conf.Store_Num_Per_User  # 每个卖家的店铺数量
        self.seller_num = conf.Seller_Num  # 卖家数量
        self.buyer_num = conf.Buyer_Num  # 买家数量
        self.session = conf.Session  # 并发会话数量
        self.stock_level = conf.Default_Stock_Level  # 初始库存数量
        self.user_funds = conf.Default_User_Funds  # 买家初始资金
        self.batch_size = conf.Data_Batch_Size  # 批量加载数据的大小
        self.procedure_per_session = conf.Request_Per_Session  # 每个会话的请求数量

        # 性能统计指标
        self.n_new_order = 0  # 总创建订单数
        self.n_payment = 0  # 总支付订单数
        self.n_new_order_ok = 0  # 成功创建的订单数
        self.n_payment_ok = 0  # 成功支付的订单数
        self.time_new_order = 0  # 创建订单的总耗时
        self.time_payment = 0  # 支付订单的总耗时
        self.lock = threading.Lock()  # 线程锁，保证统计数据更新的安全性

        # 存储上一次的统计值，用于计算增量
        self.n_new_order_past = 0
        self.n_payment_past = 0
        self.n_new_order_ok_past = 0
        self.n_payment_ok_past = 0

    def to_seller_id_and_password(self, no: int) -> (str, str):
        """生成卖家ID和密码（包含UUID，确保唯一性）"""
        return (
            f"seller_{no}_{self.uuid}",
            f"password_seller_{no}_{self.uuid}"
        )

    def to_buyer_id_and_password(self, no: int) -> (str, str):
        """生成买家ID和密码（包含UUID，确保唯一性）"""
        return (
            f"buyer_{no}_{self.uuid}",
            f"buyer_seller_{no}_{self.uuid}"
        )

    def to_store_id(self, seller_no: int, i):
        """生成店铺ID（包含卖家编号、店铺序号和UUID）"""
        return f"store_s_{seller_no}_{i}_{self.uuid}"

    def gen_database(self):
        """生成测试数据库：创建卖家、店铺、书籍和买家数据"""
        logging.info("load data")
        # 创建卖家和店铺，并添加书籍
        for i in range(1, self.seller_num + 1):
            user_id, password = self.to_seller_id_and_password(i)
            seller = register_new_seller(user_id, password)  # 注册新卖家
            # 为每个卖家创建多个店铺
            for j in range(1, self.store_num_per_user + 1):
                store_id = self.to_store_id(i, j)
                code = seller.create_store(store_id)  # 创建店铺
                assert code == 200  # 断言店铺创建成功
                self.store_ids.append(store_id)
                self.book_ids[store_id] = []  # 初始化该店铺的书籍列表
                row_no = 0
                # 批量添加书籍到店铺
                while row_no < self.book_num_per_store:
                    books = self.book_db.get_book_info(row_no, self.batch_size)
                    if len(books) == 0:
                        break
                    for bk in books:
                        code = seller.add_book(store_id, self.stock_level, bk)  # 添加书籍
                        assert code == 200  # 断言书籍添加成功
                        self.book_ids[store_id].append(bk.id)
                    row_no += len(books)
        logging.info("seller data loaded.")

        # 创建买家并初始化资金
        for k in range(1, self.buyer_num + 1):
            user_id, password = self.to_buyer_id_and_password(k)
            buyer = register_new_buyer(user_id, password)  # 注册新买家
            buyer.add_funds(self.user_funds)  # 增加初始资金
            self.buyer_ids.append(user_id)
        logging.info("buyer data loaded.")

    def get_new_order(self) -> NewOrder:
        """生成一个随机的创建订单任务（模拟真实用户下单行为）"""
        # 随机选择一个买家
        n = random.randint(1, self.buyer_num)
        buyer_id, buyer_password = self.to_buyer_id_and_password(n)
        # 随机选择一个店铺
        store_no = int(random.uniform(0, len(self.store_ids) - 1))
        store_id = self.store_ids[store_no]
        # 随机选择1-10本不同的书籍（避免重复）
        books_count = random.randint(1, 10)
        book_id_and_count = []
        book_temp = []  # 用于去重
        for _ in range(books_count):
            book_no = int(random.uniform(0, len(self.book_ids[store_id]) - 1))
            book_id = self.book_ids[store_id][book_no]
            if book_id in book_temp:
                continue
            book_temp.append(book_id)
            count = random.randint(1, 10)  # 随机购买数量
            book_id_and_count.append((book_id, count))
        # 创建买家对象和NewOrder实例
        b = Buyer(url_prefix=conf.URL, user_id=buyer_id, password=buyer_password)
        return NewOrder(b, store_id, book_id_and_count)

    def update_stat(
        self,
        n_new_order,
        n_payment,
        n_new_order_ok,
        n_payment_ok,
        time_new_order,
        time_payment,
    ):
        """更新全局性能统计数据，并输出日志（线程安全）"""
        thread_num = len(threading.enumerate())  # 当前并发线程数
        self.lock.acquire()  # 加锁，确保统计数据更新的原子性

        # 累加统计数据
        self.n_new_order += n_new_order
        self.n_payment += n_payment
        self.n_new_order_ok += n_new_order_ok
        self.n_payment_ok += n_payment_ok
        self.time_new_order += time_new_order
        self.time_payment += time_payment

        # 计算本次更新与上次的差值（增量）
        n_new_order_diff = self.n_new_order - self.n_new_order_past
        n_payment_diff = self.n_payment - self.n_payment_past

        # 当有足够数据时，计算并输出性能指标
        if self.n_payment != 0 and self.n_new_order != 0 and (self.time_payment + self.time_new_order):
            # 计算吞吐量（TPS）和延迟（Latency）
            tps = int(
                self.n_new_order_ok
                / (
                    self.time_payment / n_payment_diff
                    + self.time_new_order / n_new_order_diff
                )
            )
            new_order_latency = self.time_new_order / self.n_new_order
            payment_latency = self.time_payment / self.n_payment

            # 输出性能日志
            logging.info(
                "TPS_C={}, NO=OK:{} Thread_num:{} TOTAL:{} LATENCY:{} , P=OK:{} Thread_num:{} TOTAL:{} LATENCY:{}".format(
                    tps,  # 订单创建吞吐量
                    self.n_new_order_ok,  # 成功创建的订单数
                    n_new_order_diff,  # 本次新增的订单数（并发数）
                    self.n_new_order,  # 总订单数
                    new_order_latency,  # 订单创建平均延迟
                    self.n_payment_ok,  # 成功支付的订单数
                    n_payment_diff,  # 本次新增的支付数（并发数）
                    self.n_payment,  # 总支付数
                    payment_latency,  # 支付平均延迟
                )
            )

        self.lock.release()  # 释放锁

        # 更新历史统计值，用于下次计算增量
        self.n_new_order_past = self.n_new_order
        self.n_payment_past = self.n_payment
        self.n_new_order_ok_past = self.n_new_order_ok
        self.n_payment_ok_past = self.n_payment_ok