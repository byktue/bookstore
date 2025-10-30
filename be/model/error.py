error_code = {
    401: "authorization fail.",
    511: "non exist user id {}",
    512: "exist user id {}",
    513: "non exist store id {}",
    514: "exist store id {}",
    515: "non exist book id {}",
    516: "exist book id {}",
    517: "stock level low, book id {}",
    518: "invalid order id {}",
    519: "not sufficient funds, order id {}",
    520: "",
    521: "",
    522: "",
    523: "",
    524: "",
    525: "",
    526: "",
    527: "",
    528: "",
}


def error_non_exist_user_id(user_id):
    """返回用户ID不存在的错误码和信息"""
    return 511, error_code[511].format(user_id)


def error_exist_user_id(user_id):
    """返回用户ID已存在的错误码和信息（兼容旧格式）"""
    return 512, error_code[512].format(user_id)


def error_non_exist_store_id(store_id):
    """返回店铺ID不存在的错误码和信息"""
    return 513, error_code[513].format(store_id)


def error_exist_store_id(store_id):
    """返回店铺ID已存在的错误码和信息"""
    return 514, error_code[514].format(store_id)


def error_non_exist_book_id(book_id):
    """返回书籍ID不存在的错误码和信息"""
    return 515, error_code[515].format(book_id)


def error_exist_book_id(book_id):
    """返回书籍ID已存在的错误码和信息"""
    return 516, error_code[516].format(book_id)


def error_stock_level_low(book_id):
    """返回书籍库存不足的错误码和信息"""
    return 517, error_code[517].format(book_id)


def error_invalid_order_id(order_id):
    """返回订单ID无效的错误码和信息"""
    return 518, error_code[518].format(order_id)


def error_not_sufficient_funds(order_id):
    """返回资金不足的错误码和信息（注意：原代码此处格式串调用错误，已修正）"""
    return 519, error_code[519].format(order_id)


def error_authorization_fail():
    """返回授权失败的错误码和信息（兼容旧格式）"""
    return 401, error_code[401]


def error_and_message(code, message):
    """直接返回自定义错误码和信息"""
    return code, message


# 以下为新格式的错误函数（与旧函数逻辑重复，建议统一使用一种格式）
def error_exist_user_id(user_id: str) -> (int, str):
    return 409, f"user id {user_id} already exists"


def error_authorization_fail() -> (int, str):
    return 401, "authorization failed"