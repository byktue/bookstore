from flask import Blueprint, request, jsonify
from be.model.order import Order

bp_order = Blueprint("order", __name__, url_prefix="/order")

@bp_order.route("/create", methods=["POST"])
def create_order():
    try:
        # 从请求中获取参数（兼容测试用例的参数格式）
        data = request.json
        user_id = data.get("user_id")
        store_id = data.get("store_id")

        # 支持两种格式：books=[(id, count)] 或 book_ids+quantities
        if "books" in data:
            # 测试用例可能传递的格式：books = [(book_id, quantity), ...]
            books = data["books"]
            book_ids = [b[0] for b in books]
            quantities = [b[1] for b in books]
        else:
            # 原始格式：book_ids 和 quantities 分开
            book_ids = data.get("book_ids", [])
            quantities = data.get("quantities", [])

        # 校验参数长度匹配
        if len(book_ids) != len(quantities):
            return jsonify({"errno": 400, "msg": "book_ids与quantities长度不匹配"}), 400

        # 调用订单创建逻辑
        order_handler = Order()
        code, msg, order_id = order_handler.create_order(user_id, store_id, book_ids, quantities)

        # 返回响应（使用errno字段匹配测试用例）
        if code == 200:
            return jsonify({
                "errno": 200,
                "msg": "ok",
                "data": {"order_id": order_id}
            })
        else:
            return jsonify({"errno": code, "msg": msg}), code

    except Exception as e:
        # 捕获所有异常，返回具体错误信息
        return jsonify({
            "errno": 500,
            "msg": f"服务器内部错误：{str(e)}"
        }), 500

@bp_order.route("/get_orders", methods=["GET"])
def get_user_orders():
    try:
        user_id = request.args.get("user_id")
        order_handler = Order()
        code, msg, orders = order_handler.get_user_orders(user_id)
        if code == 200:
            return jsonify({
                "errno": 200,
                "msg": "ok",
                "data": {"orders": orders}
            })
        else:
            return jsonify({"errno": code, "msg": msg}), code
    except Exception as e:
        return jsonify({
            "errno": 500,
            "msg": f"服务器内部错误：{str(e)}"
        }), 500

@bp_order.route("/cancel", methods=["POST"])
def cancel_order():
    try:
        user_id = request.json.get("user_id")
        order_id = request.json.get("order_id")
        order_handler = Order()
        code, msg = order_handler.cancel_order(user_id, order_id)
        return jsonify({"errno": code, "msg": msg}), code
    except Exception as e:
        return jsonify({
            "errno": 500,
            "msg": f"服务器内部错误：{str(e)}"
        }), 500