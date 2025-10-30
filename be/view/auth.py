from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import user

# 创建Flask蓝图：负责用户认证相关接口（登录、注册、登出等），URL前缀统一为/auth
bp_auth = Blueprint("auth", __name__, url_prefix="/auth")


@bp_auth.route("/login", methods=["POST"])
def login():
    """用户登录接口：接收用户ID、密码、终端标识，返回登录状态和Token"""
    # 从请求JSON中获取参数（默认值为空字符串，避免KeyError）
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    terminal = request.json.get("terminal", "")
    # 实例化User类，调用登录方法
    u = user.User()
    code, message, token = u.login(
        user_id=user_id, password=password, terminal=terminal
    )
    # 返回JSON响应：包含消息和Token，HTTP状态码为业务返回码
    return jsonify({"message": message, "token": token}), code


@bp_auth.route("/logout", methods=["POST"])
def logout():
    """用户登出接口：接收用户ID和请求头中的Token，使当前Token失效"""
    # 从请求JSON获取用户ID，从请求头获取Token（符合认证接口常见设计）
    user_id: str = request.json.get("user_id")
    token: str = request.headers.get("token")
    # 实例化User类，调用登出方法
    u = user.User()
    code, message = u.logout(user_id=user_id, token=token)
    # 返回JSON响应：包含结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code


@bp_auth.route("/register", methods=["POST"])
def register():
    """用户注册接口：接收用户ID和密码，创建新用户记录"""
    # 从请求JSON中获取注册参数（默认值为空字符串）
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    # 实例化User类，调用注册方法
    u = user.User()
    code, message = u.register(user_id=user_id, password=password)
    # 返回JSON响应：包含注册结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code


@bp_auth.route("/unregister", methods=["POST"])
def unregister():
    """用户注销接口：接收用户ID和密码，校验后删除用户记录"""
    # 从请求JSON中获取注销参数（默认值为空字符串）
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    # 实例化User类，调用注销方法
    u = user.User()
    code, message = u.unregister(user_id=user_id, password=password)
    # 返回JSON响应：包含注销结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code


@bp_auth.route("/password", methods=["POST"])
def change_password():
    """密码修改接口：接收用户ID、旧密码、新密码，校验后更新密码"""
    # 从请求JSON中获取参数（注意旧密码参数名是oldPassword，与前端需对齐）
    user_id = request.json.get("user_id", "")
    old_password = request.json.get("oldPassword", "")
    new_password = request.json.get("newPassword", "")
    # 实例化User类，调用修改密码方法
    u = user.User()
    code, message = u.change_password(
        user_id=user_id, old_password=old_password, new_password=new_password
    )
    # 返回JSON响应：包含修改结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code