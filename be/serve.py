import logging
import os
from flask import Flask
from flask import Blueprint
from flask import request
from be.view import auth
from be.view import seller
from be.view import buyer
from be.model.store import init_database, init_completed_event

# 创建用于服务器关闭的蓝图
bp_shutdown = Blueprint("shutdown", __name__)


def shutdown_server():
    """关闭Werkzeug服务器的内部函数"""
    # 从请求环境中获取服务器 shutdown 函数
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


@bp_shutdown.route("/shutdown")
def be_shutdown():
    """提供HTTP接口用于触发服务器关闭"""
    shutdown_server()
    return "Server shutting down..."


def be_run():
    """启动后端服务的入口函数"""
    # 计算项目路径（当前文件所在目录的父目录）
    this_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(this_path)
    # 日志文件路径（父目录下的app.log）
    log_file = os.path.join(parent_path, "app.log")
    
    # 初始化数据库（传入父目录路径作为数据库存储路径）
    init_database(parent_path)

    # 配置日志：同时输出到文件和控制台
    logging.basicConfig(filename=log_file, level=logging.ERROR)  # 日志级别为ERROR
    # 添加控制台输出 handler
    handler = logging.StreamHandler()
    # 日志格式：时间、线程名、级别、消息
    formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)  # 注册控制台handler

    # 创建Flask应用实例
    app = Flask(__name__)
    # 注册蓝图：包含关闭服务器、认证、卖家、买家相关接口
    app.register_blueprint(bp_shutdown)
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller)
    app.register_blueprint(buyer.bp_buyer)
    
    # 标记数据库初始化完成（用于线程同步）
    init_completed_event.set()
    
    # 启动Flask开发服务器（默认地址127.0.0.1:5000）
    app.run()