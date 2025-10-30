# coding=utf-8

from lxml import etree
import sqlite3
import re
import requests
import random
import time
import logging

# 用户代理列表，模拟不同浏览器/设备的请求头
user_agent = [
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 "
    "Safari/534.50",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 "
    "Safari/534.50",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR "
    "3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
    "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
    "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 "
    "Safari/535.11",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET "
    "CLR 2.0.50727; SE 2.X MetaSr 1.0)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
    "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) "
    "Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) "
    "Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) "
    "Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
    "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) "
    "Version/4.0 Mobile Safari/533.1",
    "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) "
    "AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
    "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
    "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) "
    "Version/4.0 Safari/534.13",
    "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 "
    "Mobile Safari/534.1+",
    "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) "
    "wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
    "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) "
    "AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
    "UCWEB7.0.2.37/28/999",
    "NOKIA5700/ UCWEB7.0.2.37/28/999",
    "Openwave/ UCWEB7.0.2.37/28/999",
    "Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999",
    # iPhone 6：
    "Mozilla/6.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 "
    "Mobile/10A5376e Safari/8536.25",
]


def get_user_agent():
    """随机获取一个用户代理头，避免被目标网站识别为爬虫"""
    headers = {"User-Agent": random.choice(user_agent)}
    return headers


class Scraper:
    """豆瓣图书爬虫类，用于抓取图书标签、列表及详情信息并存储到SQLite数据库"""
    database: str  # 数据库文件路径
    tag: str       # 当前抓取的标签
    page: int      # 当前抓取的页码
    pattern_number = re.compile(r"\d+\.?\d*")  # 提取数字的正则表达式

    def __init__(self):
        self.database = "book.db"  # 默认数据库路径
        self.tag = ""
        self.page = 0
        # 配置日志：仅记录错误信息到scraper.log
        logging.basicConfig(filename="scraper.log", level=logging.ERROR)

    def get_current_progress(self) -> (str, int):
        """从数据库获取上次抓取的进度（标签和页码），用于断点续爬"""
        conn = sqlite3.connect(self.database)
        results = conn.execute("SELECT tag, page from progress where id = '0'")
        for row in results:
            return row[0], row[1]
        return "", 0

    def save_current_progress(self, current_tag, current_page):
        """保存当前抓取进度到数据库，支持断点续爬"""
        conn = sqlite3.connect(self.database)
        conn.execute(
            "UPDATE progress set tag = '{}', page = {} where id = '0'".format(
                current_tag, current_page
            )
        )
        conn.commit()
        conn.close()

    def start_grab(self) -> bool:
        """启动抓取流程：初始化数据库 -> 获取标签 -> 按标签分页抓取图书"""
        self.create_tables()  # 创建必要的数据库表
        self.grab_tag()      # 抓取图书标签列表
        current_tag, current_page = self.get_current_progress()  # 读取上次进度
        tags = self.get_tag_list()  # 获取所有标签
        # 遍历标签并分页抓取
        for i in range(0, len(tags)):
            start_page = 0
            # 如果是上次中断的标签，从上次的页码继续
            if i == 0 and current_tag == tags[i]:
                start_page = current_page
            # 分页抓取当前标签下的图书，每次20条
            while self.grab_book_list(tags[i], start_page):
                start_page += 20
        return True

    def create_tables(self):
        """创建数据库表：标签表、图书信息表、进度表"""
        conn = sqlite3.connect(self.database)
        try:
            # 标签表：存储图书分类标签
            conn.execute("CREATE TABLE tags (tag TEXT PRIMARY KEY)")
            conn.commit()
        except sqlite3.Error as e:
            logging.error(str(e))
            conn.rollback()

        try:
            # 图书信息表：存储详细图书信息
            conn.execute(
                "CREATE TABLE book ("
                "id TEXT PRIMARY KEY, title TEXT, author TEXT, "
                "publisher TEXT, original_title TEXT, "
                "translator TEXT, pub_year TEXT, pages INTEGER, "
                "price INTEGER, currency_unit TEXT, binding TEXT, "
                "isbn TEXT, author_intro TEXT, book_intro text, "
                "content TEXT, tags TEXT, picture BLOB)"
            )
            conn.commit()
        except sqlite3.Error as e:
            logging.error(str(e))
            conn.rollback()

        try:
            # 进度表：记录抓取进度，支持断点续爬
            conn.execute(
                "CREATE TABLE progress (id TEXT PRIMARY KEY, tag TEXT, page integer )"
            )
            conn.execute("INSERT INTO progress values('0', '', 0)")
            conn.commit()
        except sqlite3.Error as e:
            logging.error(str(e))
            conn.rollback()

    def grab_tag(self):
        """抓取豆瓣图书的所有分类标签并存储到tags表"""
        url = "https://book.douban.com/tag/?view=cloud"
        r = requests.get(url, headers=get_user_agent())
        r.encoding = "utf-8"
        h: etree.ElementBase = etree.HTML(r.text)
        # 解析页面，提取所有标签的链接
        tags: [] = h.xpath(
            '/html/body/div[@id="wrapper"]/div[@id="content"]'
            '/div[@class="grid-16-8 clearfix"]/div[@class="article"]'
            '/div[@class=""]/div[@class="indent tag_cloud"]'
            "/table/tbody/tr/td/a/@href"
        )
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        try:
            # 提取标签名称并插入数据库
            for tag in tags:
                t: str = tag.strip("/tag")  # 从链接中提取标签名
                c.execute("INSERT INTO tags VALUES ('{}')".format(t))
            c.close()
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logging.error(str(e))
            conn.rollback()
            return False
        return True

    def grab_book_list(self, tag="小说", pageno=1) -> bool:
        """抓取指定标签下某一页的图书列表，返回是否有下一页"""
        logging.info("开始抓取标签 {} 第 {} 页...".format(tag, pageno))
        self.save_current_progress(tag, pageno)  # 保存当前进度
        # 构造分页URL（每页20条）
        url = "https://book.douban.com/tag/{}?start={}&type=T".format(tag, pageno)
        r = requests.get(url, headers=get_user_agent())
        r.encoding = "utf-8"
        h: etree.Element = etree.HTML(r.text)

        # 提取当前页所有图书的详情页链接
        book_links: [] = h.xpath(
            '/html/body/div[@id="wrapper"]/div[@id="content"]'
            '/div[@class="grid-16-8 clearfix"]'
            '/div[@class="article"]/div[@id="subject_list"]'
            '/ul/li/div[@class="info"]/h2/a/@href'
        )
        # 判断是否有下一页
        next_page = h.xpath(
            '/html/body/div[@id="wrapper"]/div[@id="content"]'
            '/div[@class="grid-16-8 clearfix"]'
            '/div[@class="article"]/div[@id="subject_list"]'
            '/div[@class="paginator"]/span[@class="next"]/a[@href]'
        )
        has_next = len(next_page) > 0

        if len(book_links) == 0:
            return False  # 没有图书链接，停止抓取

        # 遍历图书链接，抓取详情
        for link in book_links:
            link.strip("")
            book_id = link.strip("/").split("/")[-1]  # 从链接中提取图书ID
            try:
                # 随机延迟0-2秒，避免请求过于频繁被封禁
                delay = float(random.randint(0, 200)) / 100.0
                time.sleep(delay)
                self.crow_book_info(book_id)  # 抓取单本图书详情
            except BaseException as e:
                logging.error("抓取图书 {} 失败: {}".format(book_id, str(e)))
        return has_next  # 返回是否有下一页

    def get_tag_list(self) -> [str]:
        """从数据库获取所有标签列表，用于按标签抓取"""
        ret = []
        conn = sqlite3.connect(self.database)
        # 只获取大于等于上次中断标签的标签，实现断点续爬
        results = conn.execute(
            "SELECT tags.tag from tags join progress where tags.tag >= progress.tag"
        )
        for row in results:
            ret.append(row[0])
        return ret

    def crow_book_info(self, book_id) -> bool:
        """抓取单本图书的详细信息并存储到数据库"""
        # 检查该图书是否已抓取，避免重复
        conn = sqlite3.connect(self.database)
        for _ in conn.execute("SELECT id from book where id = ('{}')".format(book_id)):
            return True  # 已存在，直接返回

        # 抓取图书详情页
        url = "https://book.douban.com/subject/{}/".format(book_id)
        r = requests.get(url, headers=get_user_agent())
        r.encoding = "utf-8"
        h: etree.Element = etree.HTML(r.text)

        # 提取图书标题
        title_elements = h.xpath('/html/body/div[@id="wrapper"]/h1/span/text()')
        if len(title_elements) == 0:
            return False  # 标题不存在，抓取失败
        title = title_elements[0]

        # 提取图书基本信息容器
        article_elements = h.xpath(
            '/html/body/div[@id="wrapper"]'
            '/div[@id="content"]/div[@class="grid-16-8 clearfix"]'
            '/div[@class="article"]'
        )
        if len(article_elements) == 0:
            return False
        e_article = article_elements[0]

        # 提取图书简介、作者简介、目录
        book_intro = ""
        author_intro = ""
        content = ""
        tags = ""

        # 图书简介
        intro_elements = e_article.xpath(
            'div[@class="related_info"]'
            '/div[@class="indent"][@id="link-report"]/*'
            '/div[@class="intro"]/*/text()'
        )
        for line in intro_elements:
            line = line.strip()
            if line:
                book_intro += line + "\n"

        # 作者简介
        author_elements = e_article.xpath(
            'div[@class="related_info"]'
            '/div[@class="indent "]/*'
            '/div[@class="intro"]/*/text()'
        )
        for line in author_elements:
            line = line.strip()
            if line:
                author_intro += line + "\n"

        # 目录
        content_elements = e_article.xpath(
            f'div[@class="related_info"]'
            f'/div[@class="indent"][@id="dir_{book_id}_full"]/text()'
        )
        for line in content_elements:
            line = line.strip()
            if line:
                content += line + "\n"

        # 图书标签
        tag_elements = e_article.xpath(
            'div[@class="related_info"]/'
            'div[@id="db-tags-section"]/'
            'div[@class="indent"]/span/a/text()'
        )
        for line in tag_elements:
            line = line.strip()
            if line:
                tags += line + "\n"

        # 提取图书封面图片
        subject_elements = e_article.xpath(
            'div[@class="indent"]'
            '/div[@class="subjectwrap clearfix"]'
            '/div[@class="subject clearfix"]'
        )
        picture = None
        if subject_elements:
            pic_href = subject_elements[0].xpath('div[@id="mainpic"]/a/@href')
            if pic_href:
                res = requests.get(pic_href[0], headers=get_user_agent())
                picture = res.content  # 图片二进制数据

        # 解析图书详细信息（作者、出版社、价格等）
        info_children = e_article.xpath(
            'div[@class="indent"]'
            '/div[@class="subjectwrap clearfix"]'
            '/div[@class="subject clearfix"]'
            '/div[@id="info"]/child::node()'
        )

        # 解析info区域的标签和内容
        e_array = []
        e_dict = dict()
        for e in info_children:
            if isinstance(e, etree._ElementUnicodeResult):
                e_dict["text"] = e  # 文本内容
            elif isinstance(e, etree._Element):
                if e.tag == "br":  # 换行符作为分隔符
                    e_array.append(e_dict)
                    e_dict = dict()
                else:
                    e_dict[e.tag] = e  # 标签元素
        e_array.append(e_dict)  # 最后一组信息

        # 提取结构化信息（作者、出版社、定价等）
        book_info = dict()
        for d in e_array:
            label = ""
            span = d.get("span")
            if span is not None:
                # 从span标签中提取标签名
                a_label = span.xpath("span/text()")
                if not label and a_label:
                    label = a_label[0].strip()
                a_label = span.xpath("text()")
                if not label and a_label:
                    label = a_label[0].strip()
                label = label.strip(":")  # 去除冒号
            # 提取文本内容
            text = d.get("text", "").strip().strip(":")
            # 处理作者/译者（可能在a标签中）
            if label in ["作者", "译者"] and not text:
                a = span.xpath("a/text()")
                if a:
                    text = a[0].strip()
                else:
                    e_a = d.get("a")
                    if e_a is not None:
                        text_a = e_a.xpath("text()")
                        if text_a:
                            text = text_a[0].strip()
                            text = re.sub(r"\s+", " ", text)
            if text:
                book_info[label] = text

        # 处理价格（转换为分，便于存储）
        unit = None
        price = None
        s_price = book_info.get("定价")
        if not s_price:
            logging.error(f"图书 {book_id} 未找到价格信息")
            return False
        else:
            # 提取数字部分
            price_match = re.findall(self.pattern_number, s_price)
            if price_match:
                number = price_match[0]
                unit = s_price.replace(number, "").strip()  # 货币单位（元）
                price = int(float(number) * 100)  # 转换为分

        # 处理页数（整数）
        pages = None
        s_pages = book_info.get("页数")
        if s_pages:
            page_match = re.findall(self.pattern_number, s_pages)
            if page_match:
                pages = int(page_match[0])

        # 插入数据库
        sql = (
            "INSERT INTO book("
            "id, title, author, "
            "publisher, original_title, translator, "
            "pub_year, pages, price, "
            "currency_unit, binding, isbn, "
            "author_intro, book_intro, content, "
            "tags, picture)"
            "VALUES("
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?, ?, "
            "?, ?)"
        )

        conn = sqlite3.connect(self.database)
        try:
            conn.execute(
                sql,
                (
                    book_id,
                    title,
                    book_info.get("作者"),
                    book_info.get("出版社"),
                    book_info.get("原作名"),
                    book_info.get("译者"),
                    book_info.get("出版年"),
                    pages,
                    price,
                    unit,
                    book_info.get("装帧"),
                    book_info.get("ISBN"),
                    author_intro,
                    book_intro,
                    content,
                    tags,
                    picture,
                ),
            )
            conn.commit()
        except sqlite3.Error as e:
            logging.error(str(e))
            conn.rollback()
            return False
        except TypeError as e:
            logging.error(f"抓取图书 {book_id} 时类型错误: {str(e)}")
            conn.rollback()
            return False
        conn.close()
        return True


if __name__ == "__main__":
    scraper = Scraper()
    scraper.database = "fe/data/book.db"  # 设置数据库路径
    scraper.start_grab()  # 启动抓取