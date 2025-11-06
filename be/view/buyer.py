from flask import Blueprint, request, jsonify
from be.model.buyer import Buyer

bp_buyer = Blueprint("buyer", __name__, url_prefix="/buyer")


@bp_buyer.route("/new_order", methods=["POST"])
def new_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    books: [] = request.json.get("books")
    id_and_count = []
    for book in books:
        book_id = book.get("id")
        count = book.get("count")
        id_and_count.append((book_id, count))

    b = Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    return jsonify({"message": message, "order_id": order_id}), code


@bp_buyer.route("/payment", methods=["POST"])
def payment():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    password: str = request.json.get("password")
    b = Buyer()
    code, message = b.payment(user_id, password, order_id)
    return jsonify({"message": message}), code


@bp_buyer.route("/add_funds", methods=["POST"])
def add_funds():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    add_value = request.json.get("add_value")
    b = Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    return jsonify({"message": message}), code


@bp_buyer.route('/receive_order', methods=['POST'])
def receive_order():
    """买家确认收货接口：更新订单状态为已收货"""
    # 提取参数，保持与现有接口一致的request.json.get()风格
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    token: str = request.json.get("token")

    # 验证必填参数（适配项目既有校验逻辑）
    if not all([user_id, order_id, token]):
        return jsonify({"message": "missing required fields"}), 400

    # 调用Buyer类的收货方法，复用现有实例化方式
    b = Buyer()
    code, message = b.receive_order(user_id, order_id, token)

    # 保持返回格式统一：仅返回message字段，状态码使用业务逻辑返回的code
    return jsonify({"message": message}), code