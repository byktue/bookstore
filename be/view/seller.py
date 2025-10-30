from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import seller
import json

# 创建Flask蓝图：负责卖家相关接口（创建店铺、添加书籍、增加库存等），URL前缀统一为/seller
bp_seller = Blueprint("seller", __name__, url_prefix="/seller")


@bp_seller.route("/create_store", methods=["POST"])
def seller_create_store():
    """创建店铺接口：接收卖家用户ID和店铺ID，创建新店铺"""
    # 从请求JSON中获取参数
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    
    # 实例化Seller类，调用创建店铺方法
    s = seller.Seller()
    code, message = s.create_store(user_id, store_id)
    
    # 返回JSON响应：包含创建结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code


@bp_seller.route("/add_book", methods=["POST"])
def seller_add_book():
    """添加书籍接口：接收卖家信息、店铺信息、书籍详情和库存，添加书籍到店铺"""
    # 从请求JSON中获取参数
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_info: str = request.json.get("book_info")  # 书籍详情（字典格式，包含"id"等字段）
    stock_level: str = request.json.get("stock_level", 0)  # 库存数量，默认0
    
    # 实例化Seller类，调用添加书籍方法（将书籍信息转为JSON字符串存储）
    s = seller.Seller()
    code, message = s.add_book(
        user_id, store_id, book_info.get("id"), json.dumps(book_info), stock_level
    )
    
    # 返回JSON响应：包含添加结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code


@bp_seller.route("/add_stock_level", methods=["POST"])
def add_stock_level():
    """增加库存接口：接收卖家信息、店铺信息、书籍ID和增加数量，更新书籍库存"""
    # 从请求JSON中获取参数
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_num: str = request.json.get("add_stock_level", 0)  # 增加的库存数量，默认0
    
    # 实例化Seller类，调用增加库存方法
    s = seller.Seller()
    code, message = s.add_stock_level(user_id, store_id, book_id, add_num)
    
    # 返回JSON响应：包含库存更新结果消息，HTTP状态码为业务返回码
    return jsonify({"message": message}), code