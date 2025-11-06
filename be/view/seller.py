from flask import Blueprint, request, jsonify
from be.model import seller
import json
import logging

# 统一使用现有蓝图命名规范（bp_seller）
bp_seller = Blueprint("seller", __name__, url_prefix="/seller")


@bp_seller.route("/create_store", methods=["POST"])
def seller_create_store():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    s = seller.Seller()
    code, message = s.create_store(user_id, store_id)
    return jsonify({"message": message}), code


@bp_seller.route("/add_book", methods=["POST"])
def seller_add_book():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_info: str = request.json.get("book_info")
    stock_level: str = request.json.get("stock_level", 0)

    s = seller.Seller()
    code, message = s.add_book(
        user_id, store_id, book_info.get("id"), json.dumps(book_info), stock_level
    )

    return jsonify({"message": message}), code


@bp_seller.route("/add_stock_level", methods=["POST"])
def add_stock_level():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_num: str = request.json.get("add_stock_level", 0)

    s = seller.Seller()
    code, message = s.add_stock_level(user_id, store_id, book_id, add_num)

    return jsonify({"message": message}), code


@bp_seller.route('/ship_order', methods=['POST'])
def ship_order():
    """卖家发货接口：更新订单状态为已发货"""
    # 提取请求参数（与现有接口一致使用request.json）
    seller_id: str = request.json.get("seller_id")
    store_id: str = request.json.get("store_id")
    order_id: str = request.json.get("order_id")
    token: str = request.json.get("token")

    # 验证必填参数（保持与其他接口相同的校验风格）
    if not all([seller_id, store_id, order_id, token]):
        return jsonify({"message": "missing required fields"}), 400

    # 调用seller模块的发货方法
    s = seller.Seller()
    code, message = s.ship_order(seller_id, store_id, order_id, token)

    # 保持返回格式统一（仅返回message字段，状态码使用code）
    return jsonify({"message": message}), code