import os
import sqlite3 as sqlite
import random
import base64
import simplejson as json

from pymongo import MongoClient  # 新增 MongoDB 客户端依赖


class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: [str]
    pictures: [bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []

class BookDB:
    def __init__(self, large: bool = False):
        # 移除 SQLite 路径相关代码，改为连接 MongoDB
        self.mongo_client = MongoClient("mongodb://localhost:27017/")  # MongoDB 连接地址
        self.db = self.mongo_client["bookstore"]  # 数据库名（与迁移脚本一致）
        self.collection = self.db["books"]  # 集合名（与迁移脚本一致）

    def get_book_count(self):
        # 从 MongoDB 集合中获取文档总数
        return self.collection.count_documents({})

    def get_book_info(self, start, size) -> [Book]:
        books = []
        # 从 MongoDB 分页查询数据（跳过 start 条，取 size 条）
        cursor = self.collection.find().skip(start).limit(size).sort("id", 1)  # 按 id 排序，与原逻辑一致

        for doc in cursor:
            book = Book()
            # 映射 MongoDB 文档字段到 Book 对象（字段名与迁移后的一致）
            book.id = doc["id"]
            book.title = doc["title"]
            book.author = doc["author"]
            book.publisher = doc["publisher"]
            book.original_title = doc.get("original_title", "")  # 处理可能为空的字段
            book.translator = doc.get("translator", "")
            book.pub_year = doc.get("pub_year", "")
            book.pages = doc.get("pages", 0)
            book.price = doc.get("price", 0)
            book.currency_unit = doc.get("currency_unit", "")
            book.binding = doc.get("binding", "")
            book.isbn = doc.get("isbn", "")
            book.author_intro = doc.get("author_intro", "")
            book.book_intro = doc.get("book_intro", "")
            book.content = doc.get("content", "")
            
            # 处理 tags 数组（迁移后已转为数组，直接赋值）
            book.tags = doc.get("tags", [])
            
            # 处理图片（MongoDB 中为 Binary 类型，需转为 base64）
            picture = doc.get("picture")
            if picture is not None:
                # 与原逻辑一致：随机生成 0-9 张图片
                for _ in range(0, random.randint(0, 9)):
                    encode_str = base64.b64encode(picture).decode("utf-8")
                    book.pictures.append(encode_str)
            
            books.append(book)
        
        return books

# class BookDB:
#     def __init__(self, large: bool = False):
#         parent_path = os.path.dirname(os.path.dirname(__file__))
#         self.db_s = os.path.join(parent_path, "data/book.db")
#         self.db_l = os.path.join(parent_path, "data/book_lx.db")
#         if large:
#             self.book_db = self.db_l
#         else:
#             self.book_db = self.db_s

#     def get_book_count(self):
#         conn = sqlite.connect(self.book_db)
#         cursor = conn.execute("SELECT count(id) FROM book")
#         row = cursor.fetchone()
#         return row[0]

#     def get_book_info(self, start, size) -> [Book]:
#         books = []
#         conn = sqlite.connect(self.book_db)
#         cursor = conn.execute(
#             "SELECT id, title, author, "
#             "publisher, original_title, "
#             "translator, pub_year, pages, "
#             "price, currency_unit, binding, "
#             "isbn, author_intro, book_intro, "
#             "content, tags, picture FROM book ORDER BY id "
#             "LIMIT ? OFFSET ?",
#             (size, start),
#         )
#         for row in cursor:
#             book = Book()
#             book.id = row[0]
#             book.title = row[1]
#             book.author = row[2]
#             book.publisher = row[3]
#             book.original_title = row[4]
#             book.translator = row[5]
#             book.pub_year = row[6]
#             book.pages = row[7]
#             book.price = row[8]

#             book.currency_unit = row[9]
#             book.binding = row[10]
#             book.isbn = row[11]
#             book.author_intro = row[12]
#             book.book_intro = row[13]
#             book.content = row[14]
#             tags = row[15]

#             picture = row[16]

#             for tag in tags.split("\n"):
#                 if tag.strip() != "":
#                     book.tags.append(tag)
#             for i in range(0, random.randint(0, 9)):
#                 if picture is not None:
#                     encode_str = base64.b64encode(picture).decode("utf-8")
#                     book.pictures.append(encode_str)
#             books.append(book)
#             # print(tags.decode('utf-8'))

#             # print(book.tags, len(book.picture))
#             # print(book)
#             # print(tags)

#         return books