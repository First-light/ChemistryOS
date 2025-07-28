import sys
sys.path.append('src/chemistry_os/src')
from enum import Enum

class FacilityState(Enum):
    IDLE = 0 # 空闲
    WAIT = 1 # 等待
    BUSY = 2 # 忙碌
    STOP = 3 # 停止
    ERROR = 4  # 错误

class ProjectState(Enum):
    INIT = 0  # 初始化
    READY = 1    # 准备
    RUNNING = 2  # 运行中
    PAUSE = 3    # 暂停
    QUIT = 4     # 退出
    ERROR = 5    # 错误

class ServerMod(Enum):
    NONE = 0  # 无状态
    SKIP = 1  # 跳过添加数据包的操作 用于触发式发送
    ADJUST = 2  # 执行一此后调整值为1 用于触发式发送

class BufferMod(Enum):
    NONE = 0  # 不接收
    READY = 1  # 可以接受