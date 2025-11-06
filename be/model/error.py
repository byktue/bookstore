# 错误码字典：补充订单状态相关错误描述
error_code = {
    401: "authorization fail.",
    409: "user id {} already exists",
    511: "non exist user id {}",
    513: "non exist store id {}",
    514: "exist store id {}",
    515: "non exist book id {}",
    516: "exist book id {}",
    517: "stock level low, book id {}",
    518: "invalid order id {}",
    519: "not sufficient funds, order id {}",
    520: "order not paid, order id {}",
    521: "order already shipped, order id {}",
    522: "order not shipped, order id {}",
    523: "order already received, order id {}",
    524: "invalid order status for {}, expected: {}",
}

# 授权错误
def error_authorization_fail() -> (int, str):
    return 401, error_code[401]

# 用户相关错误
def error_non_exist_user_id(user_id: str) -> (int, str):
    return 511, error_code[511].format(user_id)

def error_exist_user_id(user_id: str) -> (int, str):
    return 409, error_code[409].format(user_id)

# 店铺相关错误
def error_non_exist_store_id(store_id: str) -> (int, str):
    return 513, error_code[513].format(store_id)

def error_exist_store_id(store_id: str) -> (int, str):
    return 514, error_code[514].format(store_id)

# 图书相关错误
def error_non_exist_book_id(book_id: str) -> (int, str):
    return 515, error_code[515].format(book_id)

def error_exist_book_id(book_id: str) -> (int, str):
    return 516, error_code[516].format(book_id)

def error_stock_level_low(book_id: str) -> (int, str):
    return 517, error_code[517].format(book_id)

# 订单相关错误
def error_invalid_order_id(order_id: str) -> (int, str):
    return 518, error_code[518].format(order_id)

def error_not_sufficient_funds(order_id: str) -> (int, str):
    return 519, error_code[519].format(order_id)

def error_order_not_paid(order_id: str) -> (int, str):
    return 520, error_code[520].format(order_id)

def error_order_already_shipped(order_id: str) -> (int, str):
    return 521, error_code[521].format(order_id)

def error_order_not_shipped(order_id: str) -> (int, str):
    return 522, error_code[522].format(order_id)

def error_order_already_received(order_id: str) -> (int, str):
    return 523, error_code[523].format(order_id)

def error_invalid_order_status(order_id: str, expected: str) -> (int, str):
    return 524, error_code[524].format(order_id, expected)

# 通用错误
def error_invalid_parameter(msg: str) -> (int, str):
    """参数无效错误（新增）"""
    return 400, f"无效参数：{msg}"

def error_and_message(code: int, message: str) -> (int, str):
    return code, message