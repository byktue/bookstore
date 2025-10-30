import requests
from urllib.parse import urljoin


class Auth:
    """认证相关接口的客户端封装类，用于调用/auth前缀下的接口"""
    def __init__(self, url_prefix):
        # 初始化基础URL：拼接传入的前缀与"auth/"，确保接口路径正确
        self.url_prefix = urljoin(url_prefix, "auth/")

    def login(self, user_id: str, password: str, terminal: str) -> (int, str):
        """调用登录接口：返回状态码和Token"""
        # 构造请求JSON参数
        json = {"user_id": user_id, "password": password, "terminal": terminal}
        # 拼接完整接口URL（基础URL + "login"）
        url = urljoin(self.url_prefix, "login")
        # 发送POST请求
        r = requests.post(url, json=json)
        # 返回响应状态码和Token（从JSON响应中提取）
        return r.status_code, r.json().get("token")

    def register(self, user_id: str, password: str) -> int:
        """调用注册接口：返回状态码"""
        json = {"user_id": user_id, "password": password}
        url = urljoin(self.url_prefix, "register")
        r = requests.post(url, json=json)
        return r.status_code

    def password(self, user_id: str, old_password: str, new_password: str) -> int:
        """调用修改密码接口：返回状态码"""
        json = {
            "user_id": user_id,
            "oldPassword": old_password,  # 注意参数名与后端接口一致（驼峰式）
            "newPassword": new_password,
        }
        url = urljoin(self.url_prefix, "password")
        r = requests.post(url, json=json)
        return r.status_code

    def logout(self, user_id: str, token: str) -> int:
        """调用登出接口：返回状态码（需在请求头携带Token）"""
        json = {"user_id": user_id}
        headers = {"token": token}  # Token放在请求头中
        url = urljoin(self.url_prefix, "logout")
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def unregister(self, user_id: str, password: str) -> int:
        """调用注销接口：返回状态码"""
        json = {"user_id": user_id, "password": password}
        url = urljoin(self.url_prefix, "unregister")
        r = requests.post(url, json=json)
        return r.status_code