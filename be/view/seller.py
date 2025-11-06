from flask import Blueprint, request, jsonify
from be.model import seller
import json

bp_seller = Blueprint("seller", __name__, url_prefix="/seller")


@bp_seller.route("/create_store", methods=["POST"])
def seller_create_store():
    # 提取并验证参数
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")

    # 严格非空校验
    if not user_id or not isinstance(user_id, str) or len(user_id.strip()) == 0:
        return jsonify({"message": "invalid user_id (empty or not string)"}), 400
    if not store_id or not isinstance(store_id, str) or len(store_id.strip()) == 0:
        return jsonify({"message": "invalid store_id (empty or not string)"}), 400

    # 调用模型层创建店铺
    s = seller.Seller()
    code, message = s.create_store(user_id, store_id)
    return jsonify({"message": message}), code


@bp_seller.route("/add_book", methods=["POST"])
def seller_add_book():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_info: dict = request.json.get("book_info")
    stock_level: str = request.json.get("stock_level", 0)

    if not all([user_id, store_id, book_info]):
        return jsonify({"message": "missing required fields"}), 400
    if "id" not in book_info:
        return jsonify({"message": "book_info missing 'id'"}), 400

    try:
        stock_level = int(stock_level)
    except (ValueError, TypeError):
        return jsonify({"message": "stock_level must be integer"}), 400

    try:
        book_json_str = json.dumps(book_info)
    except Exception as e:
        return jsonify({"message": f"book_info serialize failed: {str(e)}"}), 400

    s = seller.Seller()
    code, message = s.add_book(
        user_id=user_id,
        store_id=store_id,
        book_id=book_info["id"],
        book_json_str=book_json_str,
        stock_level=stock_level
    )
    return jsonify({"message": message}), code


# 其他接口（add_stock_level/ship_order）保持不变
@bp_seller.route("/add_stock_level", methods=["POST"])
def add_stock_level():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_num: str = request.json.get("add_stock_level", 0)

    if not all([user_id, store_id, book_id]):
        return jsonify({"message": "missing required fields"}), 400
    try:
        add_num = int(add_num)
    except (ValueError, TypeError):
        return jsonify({"message": "add_stock_level must be integer"}), 400

    s = seller.Seller()
    code, message = s.add_stock_level(user_id, store_id, book_id, add_num)
    return jsonify({"message": message}), code


@bp_seller.route('/ship_order', methods=['POST'])
def ship_order():
    seller_id: str = request.json.get("seller_id")
    store_id: str = request.json.get("store_id")
    order_id: str = request.json.get("order_id")
    token: str = request.json.get("token")

    if not all([seller_id, store_id, order_id, token]):
        return jsonify({"message": "missing required fields"}), 400

    s = seller.Seller()
    code, message = s.ship_order(seller_id, store_id, order_id, token)
    return jsonify({"message": message}), code