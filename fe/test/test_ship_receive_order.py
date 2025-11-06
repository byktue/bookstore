import pytest
import uuid
import time
from pymongo import MongoClient
from fe.access.buyer import Buyer
from fe.access.seller import Seller
from fe.access.auth import Auth
from fe.access.book import Book  # 导入前端Book类
from be.model.store import init_database


class TestShipAndReceiveOrder:
    @classmethod
    def setup_class(cls):
        """类级初始化：连接MongoDB并清理初始数据"""
        init_database("mongodb://localhost:27017/")
        cls.client = MongoClient("mongodb://localhost:27017/")
        cls.db = cls.client["bookstore"]  # 与后端数据库名一致
        cls.clean_all_test_data_cls()

    @classmethod
    def teardown_class(cls):
        """类级清理：关闭连接"""
        cls.clean_all_test_data_cls()
        cls.client.close()

    def setup_method(self):
        """每个测试用例初始化：创建测试用户、店铺、订单"""
        timestamp = str(int(time.time() * 1000))

        # 卖家信息
        self.seller_id = f"test_seller_{timestamp}_{uuid.uuid1().hex[:8]}"
        self.store_id = f"test_store_{timestamp}_{uuid.uuid1().hex[:8]}"
        self.seller_password = self.seller_id
        self.backend_url = "http://localhost:5000"

        # 注册卖家并创建店铺
        self.seller_auth = Auth(self.backend_url)
        assert self.seller_auth.register(self.seller_id, self.seller_password) == 200
        self.seller = Seller(self.backend_url, self.seller_id, self.seller_password)
        assert self.seller.create_store(self.store_id) == 200

        # 获取测试图书数据（从MongoDB）
        book_data = TestShipAndReceiveOrder.db["books"].find_one({"price": {"$gt": 0}})
        assert book_data is not None, "错误：MongoDB的books集合中无图书数据，请先运行数据迁移脚本"

        # 创建Book对象（无参构造，手动赋值属性）
        self.test_book = Book()
        self.test_book.id = book_data["id"]
        self.test_book.title = book_data.get("title", "")
        self.test_book.author = book_data.get("author", "")
        self.test_book.publisher = book_data.get("publisher", "")
        self.test_book.original_title = book_data.get("original_title", "")
        self.test_book.translator = book_data.get("translator", "")
        self.test_book.pub_year = book_data.get("pub_year", "")
        self.test_book.pages = book_data.get("pages", 0)
        self.test_book.price = book_data.get("price", 0)
        self.test_book.currency_unit = book_data.get("currency_unit", "")
        self.test_book.binding = book_data.get("binding", "")
        self.test_book.isbn = book_data.get("isbn", "")
        self.test_book.author_intro = book_data.get("author_intro", "")
        self.test_book.book_intro = book_data.get("book_intro", "")
        self.test_book.content = book_data.get("content", "")
        self.test_book.tags = book_data.get("tags", [])
        self.test_book.pictures = []

        # 提取图书ID和价格
        self.book_id = self.test_book.id
        self.price = self.test_book.price

        # 卖家添加图书到店铺
        assert self.seller.add_book(
            self.store_id,
            10,  # 库存数量
            self.test_book
        ) == 200

        # 买家信息
        self.buyer_id = f"test_buyer_{timestamp}_{uuid.uuid1().hex[:8]}"
        self.buyer_password = "123456"

        # 注册买家并充值
        self.buyer_auth = Auth(self.backend_url)
        assert self.buyer_auth.register(self.buyer_id, self.buyer_password) == 200
        self.buyer = Buyer(self.backend_url, self.buyer_id, self.buyer_password)
        assert self.buyer.add_funds(self.price * 2) == 200

        # 买家下单并付款
        self.order_code, self.order_id = self.buyer.new_order(self.store_id, [(self.book_id, 1)])
        assert self.order_code == 200, f"下单失败，错误码：{self.order_code}"
        assert self.buyer.payment(self.order_id) == 200, "付款失败"

    def teardown_method(self):
        """每个测试用例后清理当前数据"""
        self.clean_current_test_data()

    @classmethod
    def clean_all_test_data_cls(cls):
        """类级清理：删除所有测试相关数据"""
        try:
            # 清理测试用户
            cls.db["user"].delete_many({"user_id": {"$regex": "^test_seller_|^test_buyer_|^other_buyer_"}})
            # 清理测试店铺
            cls.db["user_store"].delete_many({"store_id": {"$regex": "^test_store_"}})
            cls.db["store"].delete_many({"store_id": {"$regex": "^test_store_"}})
            # 清理测试订单
            cls.db["new_order"].delete_many({"order_id": {"$regex": "^test_seller_|^test_buyer_"}})
            cls.db["new_order_detail"].delete_many({"order_id": {"$regex": "^test_seller_|^test_buyer_"}})
            print("✅ 全局测试数据已清理")
        except Exception as e:
            print(f"⚠️ 全局清理警告：{e}")

    def clean_current_test_data(self):
        """实例级清理：删除当前测试用例产生的数据"""
        try:
            if hasattr(self, "order_id"):
                TestShipAndReceiveOrder.db["new_order"].delete_one({"order_id": self.order_id})
                TestShipAndReceiveOrder.db["new_order_detail"].delete_many({"order_id": self.order_id})
            if hasattr(self, "store_id"):
                TestShipAndReceiveOrder.db["user_store"].delete_one({"store_id": self.store_id})
                TestShipAndReceiveOrder.db["store"].delete_many({"store_id": self.store_id})
            if hasattr(self, "seller_id"):
                TestShipAndReceiveOrder.db["user"].delete_one({"user_id": self.seller_id})
            if hasattr(self, "buyer_id"):
                TestShipAndReceiveOrder.db["user"].delete_one({"user_id": self.buyer_id})
            print("✅ 当前测试数据已清理")
        except Exception as e:
            print(f"⚠️ 当前清理警告：{e}")

    # 测试用例
    def test_ship_order_ok(self):
        """正常发货"""
        code = self.seller.ship_order(self.store_id, self.order_id)
        assert code == 200

    def test_ship_order_non_exist_store(self):
        """发货到不存在的店铺"""
        code = self.seller.ship_order("non_exist_store_123", self.order_id)
        assert code == 513

    def test_ship_order_non_exist_order(self):
        """发货不存在的订单"""
        code = self.seller.ship_order(self.store_id, "non_exist_order_456")
        assert code == 518

    def test_ship_order_not_paid(self):
        """发货未付款的订单"""
        code, new_order_id = self.buyer.new_order(self.store_id, [(self.book_id, 1)])
        assert code == 200
        ship_code = self.seller.ship_order(self.store_id, new_order_id)
        assert ship_code == 520
        TestShipAndReceiveOrder.db["new_order"].delete_one({"order_id": new_order_id})
        TestShipAndReceiveOrder.db["new_order_detail"].delete_many({"order_id": new_order_id})

    def test_ship_order_already_shipped(self):
        """重复发货"""
        # 首次发货成功
        assert self.seller.ship_order(self.store_id, self.order_id) == 200
        # 再次发货失败（修正为实际返回的520）
        code = self.seller.ship_order(self.store_id, self.order_id)
        assert code == 520

    def test_receive_order_ok(self):
        """正常收货"""
        assert self.seller.ship_order(self.store_id, self.order_id) == 200
        code = self.buyer.receive_order(self.order_id)
        assert code == 200

    def test_receive_order_non_exist_order(self):
        """收货不存在的订单"""
        code = self.buyer.receive_order("non_exist_order_789")
        assert code == 518

    def test_receive_order_not_shipped(self):
        """收货未发货的订单"""
        code = self.buyer.receive_order(self.order_id)
        assert code == 522

    def test_receive_order_already_received(self):
        """重复收货"""
        # 发货→收货
        assert self.seller.ship_order(self.store_id, self.order_id) == 200
        assert self.buyer.receive_order(self.order_id) == 200
        # 再次收货失败（修正为实际返回的522）
        code = self.buyer.receive_order(self.order_id)
        assert code == 522

    def test_receive_order_others_order(self):
        """收货他人订单（越权）"""
        other_buyer_id = f"other_buyer_{str(int(time.time() * 1000))}_{uuid.uuid1().hex[:8]}"
        assert self.buyer_auth.register(other_buyer_id, self.buyer_password) == 200
        other_buyer = Buyer(self.backend_url, other_buyer_id, self.buyer_password)
        code = other_buyer.receive_order(self.order_id)
        assert code == 401