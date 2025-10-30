from fe import conf
from fe.access import buyer, auth


def register_new_buyer(user_id, password) -> buyer.Buyer:
    """
    注册新买家并返回Buyer实例
    
    流程：
    1. 通过Auth类注册新用户
    2. 断言注册成功（状态码200）
    3. 实例化Buyer类（内部会自动登录并获取Token）
    4. 返回Buyer实例，可直接用于后续买家操作
    
    参数：
        user_id: 新买家的用户ID
        password: 新买家的密码
    返回：
        已注册并登录的Buyer对象
    """
    # 实例化认证接口客户端
    a = auth.Auth(conf.URL)
    # 调用注册接口
    code = a.register(user_id, password)
    # 断言注册成功（若失败会抛出AssertionError）
    assert code == 200
    # 实例化买家接口客户端（内部自动完成登录）
    s = buyer.Buyer(conf.URL, user_id, password)
    return s