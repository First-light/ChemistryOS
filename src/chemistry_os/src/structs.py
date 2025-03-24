import sys
sys.path.append('src/chemistry_os/src')
from enum import Enum, auto

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