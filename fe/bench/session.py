from fe.bench.workload import Workload
from fe.bench.workload import NewOrder
from fe.bench.workload import Payment
import time
import threading


class Session(threading.Thread):
    """
    基准测试会话类（继承自线程类），模拟单个用户的并发操作流程
    主要执行创建订单和支付订单的业务流程，并记录性能指标
    """
    def __init__(self, wl: Workload):
        # 初始化线程父类
        threading.Thread.__init__(self)
        self.workload = wl  # 关联的工作负载对象（包含测试数据和配置）
        
        # 订单相关请求列表
        self.new_order_request = []  # 创建订单的请求列表
        self.payment_request = []    # 支付订单的请求列表
        
        # 计数器：记录已处理的请求数量和成功数量
        self.payment_i = 0       # 已处理的支付请求数
        self.new_order_i = 0     # 已处理的创建订单请求数
        self.payment_ok = 0      # 成功的支付请求数
        self.new_order_ok = 0    # 成功的创建订单请求数
        
        # 时间统计：记录总耗时
        self.time_new_order = 0  # 创建订单的总耗时
        self.time_payment = 0    # 支付订单的总耗时
        
        self.thread = None
        self.gen_procedure()     # 生成测试流程（初始化订单请求）

    def gen_procedure(self):
        """生成测试流程：根据工作负载配置，初始化创建订单的请求列表"""
        for i in range(0, self.workload.procedure_per_session):
            # 从工作负载中获取一个预定义的创建订单请求
            new_order = self.workload.get_new_order()
            self.new_order_request.append(new_order)

    def run(self):
        """线程启动入口：调用核心执行逻辑"""
        self.run_gut()

    def run_gut(self):
        """核心执行逻辑：依次处理创建订单请求，每处理一定数量后批量处理支付请求"""
        # 遍历所有创建订单的请求
        for new_order in self.new_order_request:
            # 记录创建订单的开始时间
            before = time.time()
            # 执行创建订单操作
            ok, order_id = new_order.run()
            # 记录结束时间并累加耗时
            after = time.time()
            self.time_new_order += after - before
            
            # 更新创建订单计数器
            self.new_order_i += 1
            if ok:
                # 若创建订单成功，生成对应的支付请求
                self.new_order_ok += 1
                payment = Payment(new_order.buyer, order_id)
                self.payment_request.append(payment)
            
            # 每处理100个订单或处理完所有订单时，批量处理支付请求并更新统计信息
            if self.new_order_i % 100 == 0 or self.new_order_i == len(self.new_order_request):
                # 向工作负载对象更新当前会话的统计数据
                self.workload.update_stat(
                    self.new_order_i,
                    self.payment_i,
                    self.new_order_ok,
                    self.payment_ok,
                    self.time_new_order,
                    self.time_payment,
                )
                
                # 处理所有累积的支付请求
                for payment in self.payment_request:
                    before = time.time()
                    ok = payment.run()
                    after = time.time()
                    self.time_payment += after - before
                    self.payment_i += 1
                    if ok:
                        self.payment_ok += 1
                
                # 清空已处理的支付请求列表
                self.payment_request = []