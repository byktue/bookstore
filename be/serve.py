import logging
import os
import traceback
from flask import Flask, request, jsonify, Blueprint
from be.view import auth
from be.view import seller
from be.view import buyer
from be.view import search
from be.view import order  # 导入订单蓝图
from be.model.store import init_database, init_completed_event, close_database

# 关闭服务蓝图
bp_shutdown = Blueprint("shutdown", __name__)

def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()

@bp_shutdown.route("/shutdown")
def be_shutdown():
    close_database()
    shutdown_server()
    return "Server shutting down..."

# 全局异常处理器
def register_global_error_handler(app):
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"errno": 404, "msg": f"接口不存在：{request.path}"}), 404

    @app.errorhandler(Exception)
    def handle_all_exceptions(e):
        error_msg = f"未捕获异常: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        return jsonify({
            "errno": 500,
            "msg": f"服务器内部错误：{str(e)}"
        }), 500

# 主启动函数
def be_run():
    # 初始化数据库
    init_database("mongodb://localhost:27017/")

    # 日志配置
    this_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(this_path)
    log_file = os.path.join(parent_path, "app.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.ERROR,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    # 创建Flask应用并注册所有蓝图
    app = Flask(__name__)
    app.register_blueprint(bp_shutdown)
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller)
    app.register_blueprint(buyer.bp_buyer)
    app.register_blueprint(search.bp_search)
    app.register_blueprint(order.bp_order)  # 注册订单蓝图

    # 注册异常处理器
    register_global_error_handler(app)
    app.config["JSON_SORT_KEYS"] = False

    # 标记初始化完成
    init_completed_event.set()

    # 启动服务
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )

if __name__ == "__main__":
    be_run()