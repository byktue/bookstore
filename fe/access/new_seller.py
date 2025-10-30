from fe import conf
from fe.access import seller, auth


def register_new_seller(user_id, password) -> seller.Seller:
    """
    注册新卖家并返回Seller实例
    
    流程：
    1. 通过Auth类注册新用户（卖家本质上也是系统用户）
    2. 断言注册成功（状态码200）
    3. 实例化Seller类（用于后续卖家相关操作）
    4. 返回Seller实例，可直接用于创建店铺、添加书籍等操作
    
    参数：
        user_id: 新卖家的用户ID
        password: 新卖家的密码
    返回：
        已注册的Seller对象
    """
    # 实例化认证接口客户端
    a = auth.Auth(conf.URL)
    # 调用注册接口（卖家需先成为系统用户）
    code = a.register(user_id, password)
    # 断言注册成功（若失败会抛出AssertionError）
    assert code == 200
    # 实例化卖家接口客户端
    s = seller.Seller(conf.URL, user_id, password)
    return s