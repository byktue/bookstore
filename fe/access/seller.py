import requests
from urllib.parse import urljoin
from fe.access import book
from fe.access.auth import Auth


class Seller:
    """卖家相关接口的客户端封装类，用于调用/seller前缀下的接口"""
    def __init__(self, url_prefix, seller_id: str, password: str):
        # 初始化基础URL：拼接传入的前缀与"seller/"
        self.url_prefix = urljoin(url_prefix, "seller/")
        self.seller_id = seller_id  # 卖家用户ID
        self.password = password    # 卖家密码
        self.terminal = "my terminal"  # 终端标识（固定值）
        self.auth = Auth(url_prefix)   # 实例化认证接口客户端
        
        # 初始化时自动登录，获取Token（断言登录成功，否则抛出异常）
        code, self.token = self.auth.login(self.seller_id, self.password, self.terminal)
        assert code == 200

    def create_store(self, store_id):
        """调用创建店铺接口：返回状态码"""
        # 构造请求参数
        json = {
            "user_id": self.seller_id,  # 卖家ID（创建者）
            "store_id": store_id        # 要创建的店铺ID
        }
        url = urljoin(self.url_prefix, "create_store")  # 完整接口URL
        headers = {"token": self.token}  # 请求头携带Token
        
        # 发送POST请求并返回状态码
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_book(self, store_id: str, stock_level: int, book_info: book.Book) -> int:
        """调用添加书籍接口：返回状态码"""
        # 构造请求参数（将Book对象转为字典）
        json = {
            "user_id": self.seller_id,
            "store_id": store_id,
            "book_info": book_info.__dict__,  # 书籍信息（Book对象的属性字典）
            "stock_level": stock_level        # 库存数量
        }
        url = urljoin(self.url_prefix, "add_book")
        headers = {"token": self.token}
        
        # 发送POST请求并返回状态码
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_stock_level(
        self, seller_id: str, store_id: str, book_id: str, add_stock_num: int
    ) -> int:
        """调用增加库存接口：返回状态码"""
        # 构造请求参数
        json = {
            "user_id": seller_id,        # 卖家ID
            "store_id": store_id,        # 店铺ID
            "book_id": book_id,          # 书籍ID
            "add_stock_level": add_stock_num  # 增加的库存数量
        }
        url = urljoin(self.url_prefix, "add_stock_level")
        headers = {"token": self.token}
        
        # 发送POST请求并返回状态码
        r = requests.post(url, headers=headers, json=json)
        return r.status_code