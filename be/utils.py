# 订单状态枚举（用整数便于存储和比较）
ORDER_STATUS = {
    "UNPAID": 1,    # 未付款
    "PAID": 2,      # 已付款
    "SHIPPED": 3,   # 已发货
    "RECEIVED": 4,  # 已收货
    "CANCELLED": 5  # 已取消（含主动取消和超时取消）
}

# 订单超时时间（单位：秒，如30分钟）
ORDER_TIMEOUT = 30 * 60
