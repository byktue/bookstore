# 系统配置参数

# 服务基础URL（后端API接口根地址）
URL = "http://127.0.0.1:5000/"

# 单个店铺的书籍数量
Book_Num_Per_Store = 2000

# 每个卖家创建的店铺数量
Store_Num_Per_User = 2

# 卖家账户数量
Seller_Num = 2

# 买家账户数量
Buyer_Num = 10

# 并发会话数量（模拟的并发用户数）
Session = 1

# 每个会话执行的请求数量
Request_Per_Session = 1000

# 书籍初始库存数量
Default_Stock_Level = 1000000

# 买家初始资金（单位：分，便于整数计算）
Default_User_Funds = 10000000

# 数据批量加载大小（用于初始化店铺书籍时的批量处理）
Data_Batch_Size = 100

# 是否使用大型书籍数据库（True表示使用从豆瓣爬取的完整图书数据）
Use_Large_DB = True