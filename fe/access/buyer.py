import requests
import simplejson
from urllib.parse import urljoin
from fe.access.auth import Auth


class Buyer:
    """买家相关接口的客户端封装类，用于调用/buyer前缀下的接口"""
    def __init__(self, url_prefix, user_id, password):
        # 初始化基础URL：拼接传入的前缀与"buyer/"
        self.url_prefix = urljoin(url_prefix, "buyer/")
        self.user_id = user_id  # 买家用户ID
        self.password = password  # 买家密码
        self.token = ""  # 登录后获取的Token
        self.terminal = "my terminal"  # 终端标识（固定值）
        self.auth = Auth(url_prefix)  # 实例化认证接口客户端
        
        # 初始化时自动登录，获取Token（断言登录成功，否则抛出异常）
        code, self.token = self.auth.login(self.user_id, self.password, self.terminal)
        assert code == 200

    def new_order(self, store_id: str, book_id_and_count: [(str, int)]) -> (int, str):
        """调用创建订单接口：返回状态码和订单ID"""
        # 格式化书籍列表为接口要求的格式（每个元素为{"id": book_id, "count": 数量}）
        books = []
        for id_count_pair in book_id_and_count:
            books.append({"id": id_count_pair[0], "count": id_count_pair[1]})
        
        # 构造请求参数
        json = {"user_id": self.user_id, "store_id": store_id, "books": books}
        url = urljoin(self.url_prefix, "new_order")  # 完整接口URL
        headers = {"token": self.token}  # 请求头携带Token
        
        # 发送POST请求
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        # 返回响应状态码和订单ID（从JSON响应中提取）
        return r.status_code, response_json.get("order_id")

    def payment(self, order_id: str):
        """调用订单支付接口：返回状态码"""
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "payment")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_funds(self, add_value: str) -> int:
        """调用余额充值接口：返回状态码"""
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "add_value": add_value,  # 充值金额（字符串类型）
        }
        url = urljoin(self.url_prefix, "add_funds")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code