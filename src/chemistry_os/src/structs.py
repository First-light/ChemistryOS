import sys
sys.path.append('src/chemistry_os/src')
from enum import Enum
from dataclasses import dataclass

class FacilityState(Enum):
    """设备状态枚举
    
    定义设备的各种运行状态
    """
    IDLE = 0    # 空闲状态，设备未在执行任何操作
    BUSY = 1    # 忙碌状态，设备正在执行操作
    STOP = 2    # 停止状态，设备被手动停止
    ERROR = 3   # 错误状态，设备出现异常

class ParserState(Enum):
    """解析器状态枚举
    
    定义命令解析器的各种工作状态
    """
    READY = 0       # 就绪状态，可以处理新命令
    INPUT_WAIT = 1  # 等待输入状态，正在等待用户输入
    STOP = 2        # 停止状态，解析器已停止工作
    ERROR = 3       # 错误状态，解析器出现异常

class ProjectState(Enum):
    """项目状态枚举
    
    定义项目执行的各种状态
    """
    INIT = 0     # 初始化状态，项目正在初始化
    READY = 1    # 准备状态，项目已准备好可以启动
    RUNNING = 2  # 运行状态，项目正在执行
    PAUSE = 3    # 暂停状态，项目被暂停
    END = 4      # 结束状态，项目已完成
    ERROR = 5    # 错误状态，项目执行出现异常

class ServerMod(Enum):
    """服务器模式枚举
    
    定义服务器的不同工作模式
    """
    NONE = 0     # 无状态，默认状态
    SKIP = 1     # 跳过模式，跳过添加数据包操作，用于触发式发送
    ADJUST = 2   # 调整模式，执行一次后调整值为1，用于触发式发送

class BufferMod(Enum):
    """缓冲区模式枚举
    
    定义缓冲区的接收状态
    """
    NONE = 0   # 不接收状态，缓冲区不接收数据
    READY = 1  # 就绪状态，缓冲区可以接收数据

@dataclass
class EquipmentID:
    """设备ID常量类
    
    定义系统中各种设备的标识符
    """
    measuring_flask: str = "measuring_flask"      # 量杯设备ID
    test_tube: str = "test_tube"                  # 试管设备ID
    three_necked_flask: str = "three_necked_flask" # 三颈烧瓶设备ID