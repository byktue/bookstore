from flask import Blueprint, request, jsonify
from be.model.order import Order

bp_order = Blueprint("order", __name__, url_prefix="/order")


@bp_order.route("/create", methods=["POST"])
def create_order():
    user_id = request.json.get("user_id")
    store_id = request.json.get("store_id")
    book_ids = request.json.get("book_ids", [])
    quantities = request.json.get("quantities", [])

    order_handler = Order()
    code, msg, order_id = order_handler.create_order(user_id, store_id, book_ids, quantities)
    if code == 200:
        return jsonify({
            "code": 200,
            "msg": "ok",
            "data": {"order_id": order_id}
        })
    else:
        return jsonify({"code": code, "msg": msg}), code


@bp_order.route("/get_orders", methods=["GET"])
def get_user_orders():
    user_id = request.args.get("user_id")
    order_handler = Order()
    code, msg, orders = order_handler.get_user_orders(user_id)
    if code == 200:
        return jsonify({
            "code": 200,
            "msg": "ok",
            "data": {"orders": orders}
        })
    else:
        return jsonify({"code": code, "msg": msg}), code


@bp_order.route("/cancel", methods=["POST"])
def cancel_order():
    user_id = request.json.get("user_id")
    order_id = request.json.get("order_id")
    order_handler = Order()
    code, msg = order_handler.cancel_order(user_id, order_id)
    return jsonify({"code": code, "msg": msg}), code