import requests
import threading
from urllib.parse import urljoin

thread: threading.Thread = None

import sys
import os

# 获取当前文件（conftest.py）的路径
current_file_path = os.path.abspath(__file__)
# 获取 fe 文件夹的路径（当前文件的父目录）
fe_dir = os.path.dirname(current_file_path)
# 获取项目根目录（fe 文件夹的父目录，即 bookstore 目录）
project_root = os.path.dirname(fe_dir)
# 将项目根目录加入 Python 搜索路径
if project_root not in sys.path:
    sys.path.append(project_root)

from be import serve
from be.model.store import init_completed_event
from fe import conf

# 修改这里启动后端程序，如果不需要可删除这行代码
def run_backend():
    # rewrite this if rewrite backend
    serve.be_run()


def pytest_configure(config):
    global thread
    print("frontend begin test")
    thread = threading.Thread(target=run_backend)
    thread.start()
    init_completed_event.wait()


def pytest_unconfigure(config):
    url = urljoin(conf.URL, "shutdown")
    requests.get(url)
    thread.join()
    print("frontend end test")
