import requests
from urllib.parse import urljoin
from fe import conf


class Order:
    def __init__(self):
        self.url_prefix = urljoin(conf.URL, "/order/")

    def create_order(self, user_id: str, store_id: str, book_ids: list, quantities: list) -> (int, dict):
        """创建订单：返回 (状态码, 结果字典)"""
        try:
            url = urljoin(self.url_prefix, "create")
            json = {
                "user_id": user_id,
                "store_id": store_id,
                "book_ids": book_ids,
                "quantities": quantities
            }
            r = requests.post(url, json=json)
            # 确保返回 (状态码, 响应JSON)
            return r.status_code, r.json()
        except Exception as e:
            # 异常时返回500和错误信息
            return 500, {"msg": f"创建订单异常: {str(e)}"}

    def get_user_orders(self, user_id: str) -> (int, dict):
        """查询用户订单：返回 (状态码, 结果字典)"""
        try:
            url = urljoin(self.url_prefix, f"get_orders?user_id={user_id}")
            r = requests.get(url)
            return r.status_code, r.json()
        except Exception as e:
            return 500, {"msg": f"查询订单异常: {str(e)}"}

    def cancel_order(self, user_id: str, order_id: str) -> (int, dict):
        """取消订单：返回 (状态码, 结果字典)"""
        try:
            url = urljoin(self.url_prefix, "cancel")
            json = {
                "user_id": user_id,
                "order_id": order_id
            }
            r = requests.post(url, json=json)
            return r.status_code, r.json()
        except Exception as e:
            return 500, {"msg": f"取消订单异常: {str(e)}"}