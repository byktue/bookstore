# 错误码字典：统一管理所有错误描述，便于前后端一致处理
# 编码规则：4xx 为客户端错误，5xx 为业务逻辑错误
error_code = {
    # 通用授权错误
    401: "authorization fail.",
    409: "user id {} already exists",  # 资源冲突（用户已存在）

    # 用户相关错误
    511: "non exist user id {}",       # 用户不存在
    512: "exist user id {}",           # 用户已存在（兼容旧逻辑，建议优先用409）

    # 店铺相关错误
    513: "non exist store id {}",      # 店铺不存在
    514: "exist store id {}",          # 店铺已存在

    # 图书相关错误
    515: "non exist book id {}",       # 图书不存在
    516: "exist book id {}",           # 图书已存在
    517: "stock level low, book id {}",# 库存不足

    # 订单相关错误
    518: "invalid order id {}",        # 无效订单ID（包含订单不存在）
    519: "not sufficient funds, order id {}",  # 余额不足
    520: "order not paid, order id {}",         # 订单未付款
    521: "order already shipped, order id {}",  # 订单已发货
    522: "order not shipped, order id {}",      # 订单未发货
    523: "order already received, order id {}", # 订单已收货
    524: "invalid order status for {}, expected: {}",  # 订单状态不合法
}


# ------------------------------
# 错误方法定义（与错误码一一对应）
# ------------------------------

def error_authorization_fail() -> (int, str):
    """授权失败（如token无效）"""
    return 401, error_code[401]


def error_non_exist_user_id(user_id: str) -> (int, str):
    """用户ID不存在"""
    return 511, error_code[511].format(user_id)


def error_exist_user_id(user_id: str) -> (int, str):
    """用户ID已存在（优先使用409冲突码）"""
    return 409, error_code[409].format(user_id)
    # 兼容旧逻辑（如需保留512编码，取消下一行注释）
    # return 512, error_code[512].format(user_id)


def error_non_exist_store_id(store_id: str) -> (int, str):
    """店铺ID不存在"""
    return 513, error_code[513].format(store_id)


def error_exist_store_id(store_id: str) -> (int, str):
    """店铺ID已存在"""
    return 514, error_code[514].format(store_id)


def error_non_exist_book_id(book_id: str) -> (int, str):
    """图书ID不存在"""
    return 515, error_code[515].format(book_id)


def error_exist_book_id(book_id: str) -> (int, str):
    """图书ID已存在"""
    return 516, error_code[516].format(book_id)


def error_stock_level_low(book_id: str) -> (int, str):
    """图书库存不足"""
    return 517, error_code[517].format(book_id)


def error_invalid_order_id(order_id: str) -> (int, str):
    """订单ID无效（格式错误等）"""
    return 518, error_code[518].format(order_id)


def error_non_exist_order_id(order_id: str) -> (int, str):
    """订单ID不存在（复用518错误码，语义更精确）"""
    return 518, error_code[518].format(order_id)


def error_not_sufficient_funds(order_id: str) -> (int, str):
    """用户余额不足（无法支付订单）"""
    return 519, error_code[519].format(order_id)


def error_order_not_paid(order_id: str) -> (int, str):
    """订单未付款（操作需要已付款状态）"""
    return 520, error_code[520].format(order_id)


def error_order_already_shipped(order_id: str) -> (int, str):
    """订单已发货（重复发货等错误）"""
    return 521, error_code[521].format(order_id)


def error_order_not_shipped(order_id: str) -> (int, str):
    """订单未发货（操作需要已发货状态）"""
    return 522, error_code[522].format(order_id)


def error_order_already_received(order_id: str) -> (int, str):
    """订单已收货（重复确认收货等错误）"""
    return 523, error_code[523].format(order_id)


def error_invalid_order_status(order_id: str, expected: str) -> (int, str):
    """订单状态不合法（当前状态与操作所需状态不符）"""
    return 524, error_code[524].format(order_id, expected)


def error_and_message(code: int, message: str) -> (int, str):
    """通用错误构造方法（用于自定义错误信息）"""
    return code, message