import jwt
import time
import logging
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn

# JWT编码逻辑：将用户ID、终端标识、时间戳封装为JWT字符串
# 生成的JWT格式对应的JSON结构：
#   {
#       "user_id": [用户ID],
#       "terminal": [终端编码],
#       "timestamp": [时间戳]
#   }
def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,  # 以用户ID作为JWT签名密钥
        algorithm="HS256",  # 使用HS256哈希算法进行签名
    )
    return encoded


# JWT解码逻辑：将JWT字符串解析为包含用户信息的JSON结构
# 解析后返回的JSON格式与编码时一致（见上方jwt_encode注释）
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # Token有效期：3600秒（1小时）

    def __init__(self):
        # 继承父类DBConn的数据库连接初始化逻辑
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        """私有方法：校验Token有效性（内部调用，不对外暴露）"""
        try:
            # 1. 先校验Token与数据库存储的是否一致
            if db_token != token:
                return False
            # 2. 解码Token并校验有效期
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]  # 获取Token生成时的时间戳
            if ts is not None:
                now = time.time()
                # 校验Token是否在有效期内（0 ≤ 当前时间-生成时间 ≤ 有效期）
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            # 捕获JWT签名无效错误（如密钥不匹配、Token被篡改）
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        """用户注册：创建新用户记录，初始化Token和终端标识"""
        try:
            # 生成唯一终端标识（用当前时间戳避免重复）
            terminal = "terminal_{}".format(str(time.time()))
            # 生成初始JWT Token
            token = jwt_encode(user_id, terminal)
            # 插入用户记录到数据库（初始余额为0）
            self.conn.execute(
                "INSERT into user(user_id, password, balance, token, terminal) "
                "VALUES (?, ?, ?, ?, ?);",
                (user_id, password, 0, token, terminal),
            )
            self.conn.commit()
        except sqlite.Error:
            # 捕获SQLite错误（大概率是用户ID已存在，触发主键冲突）
            return error.error_exist_user_id(user_id)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        """Token校验：对外提供的Token有效性检查接口"""
        # 查询数据库中该用户存储的Token
        cursor = self.conn.execute("SELECT token from user where user_id=?", (user_id,))
        row = cursor.fetchone()
        # 1. 若用户不存在（无查询结果），返回授权失败
        if row is None:
            return error.error_authorization_fail()
        db_token = row[0]
        # 2. 调用私有方法校验Token一致性和有效期
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        """密码校验：检查用户输入的密码与数据库存储的是否一致"""
        # 查询数据库中该用户的密码
        cursor = self.conn.execute(
            "SELECT password from user where user_id=?", (user_id,)
        )
        row = cursor.fetchone()
        # 1. 若用户不存在，返回授权失败
        if row is None:
            return error.error_authorization_fail()
        # 2. 若密码不匹配，返回授权失败
        if password != row[0]:
            return error.error_authorization_fail()
        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        """用户登录：校验密码，生成新Token并更新数据库"""
        token = ""
        try:
            # 1. 先校验密码是否正确
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""
            # 2. 为当前终端生成新的JWT Token
            token = jwt_encode(user_id, terminal)
            # 3. 更新数据库中的Token和终端标识
            cursor = self.conn.execute(
                "UPDATE user set token= ? , terminal = ? where user_id = ?",
                (token, terminal, user_id),
            )
            # 若更新行数为0（用户不存在），返回授权失败
            if cursor.rowcount == 0:
                return error.error_authorization_fail() + ("",)
            self.conn.commit()
        except sqlite.Error as e:
            # 捕获SQLite执行错误
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            # 捕获其他未知异常
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> (int, str):
        """用户登出：使当前Token失效（替换为无效Token）"""
        try:
            # 1. 先校验当前Token是否有效
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message
            # 2. 生成无效的终端标识和Token（用当前时间戳确保唯一性）
            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)
            # 3. 更新数据库，将原Token替换为无效Token
            cursor = self.conn.execute(
                "UPDATE user SET token = ?, terminal = ? WHERE user_id=?",
                (dummy_token, terminal, user_id),
            )
            # 若更新行数为0（用户不存在），返回授权失败
            if cursor.rowcount == 0:
                return error.error_authorization_fail()
            self.conn.commit()
        except sqlite.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        """用户注销：校验密码后删除用户记录"""
        try:
            # 1. 先校验密码是否正确
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message
            # 2. 从数据库中删除该用户记录
            cursor = self.conn.execute("DELETE from user where user_id=?", (user_id,))
            # 若删除行数为1（删除成功），提交事务；否则返回授权失败
            if cursor.rowcount == 1:
                self.conn.commit()
            else:
                return error.error_authorization_fail()
        except sqlite.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> (int, str):
        """修改密码：校验旧密码，更新新密码并重置Token"""
        try:
            # 1. 先校验旧密码是否正确
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message
            # 2. 生成新的终端标识和Token（密码修改后原Token失效）
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            # 3. 更新数据库中的密码、Token和终端标识
            cursor = self.conn.execute(
                "UPDATE user set password = ?, token= ? , terminal = ? where user_id = ?",
                (new_password, token, terminal, user_id),
            )
            # 若更新行数为0（用户不存在），返回授权失败
            if cursor.rowcount == 0:
                return error.error_authorization_fail()
            self.conn.commit()
        except sqlite.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"