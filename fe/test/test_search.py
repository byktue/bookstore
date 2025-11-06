import time
import pytest
import ast
from fe.access import search
from fe import conf
from be.model.store import get_db, init_database


class TestSearch:
    @pytest.fixture(autouse=True)
    def init_resources(self):
        init_database("mongodb://localhost:27017/")
        self.searcher = search.Search(conf.URL)
        self.db = get_db()
        yield

    @pytest.fixture(autouse=True)
    def prepare_valid_books(self):
        self.valid_books = list(self.db.books.find({
            "title": {"$exists": True, "$ne": ""},
            "tags": {"$exists": True, "$ne": ""},
            "content": {"$exists": True, "$ne": ""},
            "id": {"$exists": True},
            "store_id": {"$exists": True}
        }).limit(10))

        if len(self.valid_books) == 0:
            pytest.skip("数据库books集合中无有效图书数据！")

    @pytest.mark.parametrize("search_field", ["title", "tags", "content"])
    def test_search_by_field(self, search_field):
        sample_book = self.valid_books[0]
        book_id = sample_book["id"]

        # 提取关键字
        if search_field == "tags":
            try:
                tags_list = ast.literal_eval(sample_book["tags"])
                keyword = tags_list[0].strip() if tags_list else ""
            except:
                keyword = sample_book["tags"][:6].strip()
        else:
            keyword = sample_book[search_field][:6].strip()

        if not keyword:
            pytest.skip(f"样本图书{search_field}无有效关键字")

        # 执行搜索并容错
        status, resp = self.searcher.search_books(keyword=keyword)
        assert status == 200, f"{search_field}搜索失败：{resp}"

        # 确保data和total字段存在
        assert "data" in resp, f"响应缺少data字段：{resp}"
        data = resp["data"]
        assert "total" in data, f"响应data缺少total字段：{data}"

        # 验证结果
        assert data["total"] >= 1, f"{search_field}搜索无结果"
        assert book_id in [b["book_id"] for b in data["books"]], "未匹配样本图书"

    def test_search_scope(self):
        sample_book = self.valid_books[0]
        keyword = sample_book["title"][:5].strip()
        target_store = sample_book["store_id"]

        # 全站搜索
        all_status, all_resp = self.searcher.search_books(keyword=keyword)
        assert all_status == 200, "全站搜索失败"
        assert "data" in all_resp and "total" in all_resp["data"], "全站响应结构错误"
        all_total = all_resp["data"]["total"]
        assert all_total >= 1, "全站搜索无结果"

        # 指定店铺搜索
        store_status, store_resp = self.searcher.search_books(
            keyword=keyword,
            store_id=target_store
        )
        assert store_status == 200, "指定店铺搜索失败"
        assert "data" in store_resp and "total" in store_resp["data"], "店铺响应结构错误"
        store_total = store_resp["data"]["total"]
        assert store_total >= 1, "指定店铺无结果"
        assert store_total <= all_total, "范围筛选异常"
        assert all(b["store_id"] == target_store for b in store_resp["data"]["books"]), "店铺匹配错误"

    def test_pagination(self):
        keyword = "故事"  # 替换为实际高频词
        page_size = 2

        # 第1页
        p1_status, p1_resp = self.searcher.search_books(
            keyword=keyword,
            page_num=1,
            page_size=page_size
        )
        assert p1_status == 200, "第1页分页失败"
        assert "data" in p1_resp and "total" in p1_resp["data"], "分页响应结构错误"
        total = p1_resp["data"]["total"]
        if total <= page_size:
            pytest.skip(f"总结果不足2页（共{total}条）")

        # 第2页
        p2_status, p2_resp = self.searcher.search_books(
            keyword=keyword,
            page_num=2,
            page_size=page_size
        )
        assert p2_status == 200, "第2页分页失败"

        # 验证无重复
        p1_ids = {b["book_id"] for b in p1_resp["data"]["books"]}
        p2_ids = {b["book_id"] for b in p2_resp["data"]["books"]}
        assert len(p1_ids & p2_ids) == 0, "分页结果重复"

    def test_no_result(self):
        random_keyword = f"no_result_{hash(time.time())}"
        status, resp = self.searcher.search_books(keyword=random_keyword)
        assert status == 200, "无结果搜索失败"
        assert "data" in resp and "total" in resp["data"], "无结果响应结构错误"
        assert resp["data"]["total"] == 0, "无结果搜索异常"
        assert len(resp["data"]["books"]) == 0, "无结果返回非空列表"