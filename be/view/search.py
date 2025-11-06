from flask import Blueprint, request, jsonify
import logging
from be.model.store import get_db

bp_search = Blueprint("search", __name__)


@bp_search.route("/search_books", methods=["GET"])
def search_books():
    # 初始化默认响应结构（确保包含所有必要字段）
    default_resp = {
        "code": 200,
        "data": {
            "total": 0,
            "page_num": 1,
            "page_size": 20,
            "books": []
        }
    }

    try:
        # 解析参数（增加类型校验）
        keyword = request.args.get("keyword", "").strip()
        store_id = request.args.get("store_id", "").strip()

        # 处理页码和页大小（确保为正数）
        try:
            page_num = int(request.args.get("page_num", 1))
            page_size = int(request.args.get("page_size", 20))
            page_num = max(1, page_num)  # 页码最小为1
            page_size = max(1, min(page_size, 100))  # 页大小限制1-100
        except ValueError:
            return jsonify({
                "code": 400,
                "msg": "页码或页大小必须为整数",
                "data": default_resp["data"]  # 即使参数错误也返回完整结构
            }), 400

        # 构建查询条件
        query = {}
        if keyword:
            query["$text"] = {"$search": keyword}
        if store_id:
            query["store_id"] = store_id

        # 执行查询
        db = get_db()
        collection = db.books
        total = collection.count_documents(query)  # 计算总条数

        # 分页查询
        skip = (page_num - 1) * page_size
        cursor = collection.find(
            query,
            {
                "score": {"$meta": "textScore"},
                "store_id": 1,
                "book_id": "$id",  # 映射id为book_id
                "title": 1,
                "tags": 1,
                "price": 1
            }
        ).sort([("score", {"$meta": "textScore"})])

        # 处理结果
        books = []
        for book in cursor.skip(skip).limit(page_size):
            book.pop("_id", None)
            books.append(book)

        # 构造成功响应
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": {
                "total": total,
                "page_num": page_num,
                "page_size": page_size,
                "books": books
            }
        })

    except Exception as e:
        logging.error(f"搜索异常: {str(e)}")
        # 异常时仍返回完整结构（total=0）
        return jsonify({
            "code": 500,
            "msg": f"搜索失败：{str(e)}",
            "data": default_resp["data"]
        }), 500