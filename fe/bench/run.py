from fe.bench.workload import Workload
from fe.bench.session import Session


def run_bench():
    """
    运行基准测试的主函数
    
    流程：
    1. 生成测试工作负载（初始化测试数据）
    2. 创建多个会话（模拟多用户并发）
    3. 启动所有会话执行测试任务
    4. 等待所有会话完成并汇总结果
    """
    # 初始化工作负载：生成测试所需的数据库数据（如用户、店铺、书籍等）
    wl = Workload()
    wl.gen_database()

    # 创建会话列表：根据工作负载配置的会话数量，实例化多个Session对象
    sessions = []
    for i in range(0, wl.session):
        ss = Session(wl)  # 每个会话关联到同一工作负载
        sessions.append(ss)

    # 启动所有会话：并发执行测试任务（每个Session可能在独立线程中运行）
    for ss in sessions:
        ss.start()

    # 等待所有会话完成：阻塞当前线程，直到所有测试会话执行结束
    for ss in sessions:
        ss.join()


# 若直接运行该脚本，则执行基准测试
# if __name__ == "__main__":
#    run_bench()