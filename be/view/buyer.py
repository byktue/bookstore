from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.buyer import Buyer

# 创建Flask蓝图：负责买家相关接口（创建订单、支付、充值等），URL前缀统一为/buyer
bp_buyer = Blueprint("buyer", __name__, url_prefix="/buyer")


@bp_buyer.route("/new_order", methods=["POST"])
def new_order():
    """创建新订单接口：接收用户ID、店铺ID和书籍列表，返回订单ID"""
    # 从请求JSON中获取参数
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    books: [] = request.json.get("books")  # 书籍列表，每个元素包含"id"（书籍ID）和"count"（购买数量）
    
    # 解析书籍列表为(book_id, count)元组列表
    id_and_count = []
    for book in books:
        book_id = book.get("id")
        count = book.get("count")
        id_and_count.append((book_id, count))
    
    # 实例化Buyer类，调用创建订单方法
    b = Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    
    # 返回JSON响应：包含结果消息和订单ID，HTTP状态码为业务返回码
    return jsonify({"message": message, "order_id": order_id}), code


@bp_buyer.route("/payment", methods=["POST"])
def payment():
    """订单支付接口：接收用户ID、订单ID和密码，完成支付流程"""
    # 从请求JSON中获取参数
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    password: str = request.json.get("password")
    
    # 实例化Buyer类，调用支付方法
    b = Buyer()
    code, message = b.payment(user_id, password, order_id)
    
    # 返回JSON响应：包含支付结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code


@bp_buyer.route("/add_funds", methods=["POST"])
def add_funds():
    """余额充值接口：接收用户ID、密码和充值金额，增加用户余额"""
    # 从请求JSON中获取参数
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    add_value = request.json.get("add_value")  # 充值金额
    
    # 实例化Buyer类，调用充值方法
    b = Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    
    # 返回JSON响应：包含充值结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code