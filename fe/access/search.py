# fe/access/search.py
import requests
from fe.conf import URL  # 保留默认URL

class Search:
    # 支持传入自定义URL，默认使用conf.URL
    def __init__(self, url_prefix=None):
        self.url_prefix = url_prefix if url_prefix else URL

    def search_books(self, keyword, store_id="", page_num=1, page_size=20):
        search_url = f"{self.url_prefix}/search_books"
        params = {
            "keyword": keyword,
            "store_id": store_id,
            "page_num": page_num,
            "page_size": page_size
        }
        try:
            response = requests.get(search_url, params=params, timeout=10)
            return response.status_code, response.json()
        except Exception as e:
            return 500, {"msg": f"搜索请求失败：{str(e)}"}