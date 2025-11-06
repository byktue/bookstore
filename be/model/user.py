import jwt
import time
import logging
from pymongo import MongoClient
from be.model import error
from be.model.store import get_db  # 复用 MongoDB 数据库连接


# JWT 编码（保持不变）
def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded


# JWT 解码（保持不变）
def jwt_decode(encoded_token, user_id: str) -> dict:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms=["HS256"])
    return decoded


class User:
    token_lifetime: int = 3600  # 令牌有效期（3600秒）

    def __init__(self):
        # 通过全局方法获取 MongoDB 数据库实例
        self.db = get_db()
        # 用户集合（对应原 SQL user 表）
        self.user_col = self.db['user']

    def __check_token(self, user_id: str, db_token: str, token: str) -> bool:
        """验证令牌有效性（内部方法）"""
        try:
            # 令牌不匹配直接失败
            if db_token != token:
                return False
            # 解码令牌
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            # 验证令牌有效期
            ts = jwt_text.get("timestamp")
            if ts is None:
                return False
            now = time.time()
            # 令牌在有效期内（0 <= 现在-时间戳 <= 有效期）
            return 0 <= now - ts <= self.token_lifetime
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(f"令牌签名错误: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"令牌验证失败: {str(e)}")
            return False

    def register(self, user_id: str, password: str) -> (int, str):
        """用户注册"""
        try:
            # 检查用户是否已存在
            if self.user_col.find_one({"user_id": user_id}):
                return error.error_exist_user_id(user_id)

            # 生成初始终端和令牌
            terminal = f"terminal_{time.time()}"
            token = jwt_encode(user_id, terminal)

            # 插入新用户
            self.user_col.insert_one({
                "user_id": user_id,
                "password": password,
                "balance": 0,  # 初始余额为0
                "token": token,
                "terminal": terminal
            })
            return 200, "ok"
        except Exception as e:
            logging.error(f"注册失败: {str(e)}")
            return 530, f"系统错误: {str(e)}"

    def check_token(self, user_id: str, token: str) -> (int, str):
        """验证令牌"""
        try:
            # 查询用户
            user = self.user_col.find_one({"user_id": user_id})
            if not user:
                return error.error_authorization_fail()

            # 验证令牌
            db_token = user["token"]
            if not self.__check_token(user_id, db_token, token):
                return error.error_authorization_fail()

            return 200, "ok"
        except Exception as e:
            logging.error(f"令牌检查失败: {str(e)}")
            return 530, f"系统错误: {str(e)}"

    def check_password(self, user_id: str, password: str) -> (int, str):
        """验证密码"""
        try:
            # 查询用户
            user = self.user_col.find_one({"user_id": user_id})
            if not user:
                return error.error_authorization_fail()

            # 验证密码
            if user["password"] != password:
                return error.error_authorization_fail()

            return 200, "ok"
        except Exception as e:
            logging.error(f"密码检查失败: {str(e)}")
            return 530, f"系统错误: {str(e)}"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        """用户登录"""
        token = ""
        try:
            # 验证密码
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            # 生成新令牌
            token = jwt_encode(user_id, terminal)

            # 更新用户令牌和终端
            result = self.user_col.update_one(
                {"user_id": user_id},
                {"$set": {"token": token, "terminal": terminal}}
            )
            if result.modified_count == 0:
                return error.error_authorization_fail() + ("",)

            return 200, "ok", token
        except Exception as e:
            logging.error(f"登录失败: {str(e)}")
            return 530, f"系统错误: {str(e)}", ""

    def logout(self, user_id: str, token: str) -> (int, str):
        """用户登出"""
        try:
            # 验证令牌
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            # 生成无效令牌（登出后令牌失效）
            terminal = f"terminal_{time.time()}"
            dummy_token = jwt_encode(user_id, terminal)

            # 更新令牌为无效值
            result = self.user_col.update_one(
                {"user_id": user_id},
                {"$set": {"token": dummy_token, "terminal": terminal}}
            )
            if result.modified_count == 0:
                return error.error_authorization_fail()

            return 200, "ok"
        except Exception as e:
            logging.error(f"登出失败: {str(e)}")
            return 530, f"系统错误: {str(e)}"

    def unregister(self, user_id: str, password: str) -> (int, str):
        """用户注销"""
        try:
            # 验证密码
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            # 删除用户
            result = self.user_col.delete_one({"user_id": user_id})
            if result.deleted_count == 0:
                return error.error_authorization_fail()

            return 200, "ok"
        except Exception as e:
            logging.error(f"注销失败: {str(e)}")
            return 530, f"系统错误: {str(e)}"

    def change_password(
            self, user_id: str, old_password: str, new_password: str
    ) -> (int, str):
        """修改密码"""
        try:
            # 验证旧密码
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            # 生成新终端和令牌（密码修改后旧令牌失效）
            terminal = f"terminal_{time.time()}"
            token = jwt_encode(user_id, terminal)

            # 更新密码和令牌
            result = self.user_col.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "password": new_password,
                        "token": token,
                        "terminal": terminal
                    }
                }
            )
            if result.modified_count == 0:
                return error.error_authorization_fail()

            return 200, "ok"
        except Exception as e:
            logging.error(f"密码修改失败: {str(e)}")
            return 530, f"系统错误: {str(e)}"