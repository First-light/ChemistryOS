import socket
import threading
import json
import datetime
import time
from typing import Dict, Any, Callable, Optional, Union
from facility import Facility

class TCPServer(Facility):
    """
    TCP服务端类，提供连接、发送和接收数据的功能。
    """
    type = "tcp_server"
    data_units = []

    def __init__(self,name: str = "server",host: str = '0.0.0.0', port: int = 8888, buffer_size: int = 4096):
        """
        初始化TCP服务端
        """
        super().__init__(name, type = TCPServer.type)
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.is_running = False
        self.is_connected = False
        self.tx_buffer = []
        self.rx_buffer = []
        self.callback = None
        self.pkg_ID = 0
        self.loop_time = 0.1  # 发送和接收数据的循环时间间隔
        self.units_init()
        self.file_timestape = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def cmd_init(self):
        pass

    def units_init(self):
        pass
        # self.register("temperature_unit", 10, {"temperature": 25.0})
        # self.register("pressure_unit", 3, {"pressure": 101.3})

    def start(self):
        """
        启动TCP服务端，开始监听连接并处理数据。
        """
        try:
            # 创建一个TCP/IP套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置套接字选项，允许地址重用
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 绑定套接字到指定的主机和端口
            self.server_socket.bind((self.host, self.port))
            # 开始监听传入的连接，最大连接数为1
            self.server_socket.listen(1)
            # 设置服务器运行状态为True
            self.is_running = True

            self.log.info(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            self.log.info("等待客户端连接...")
            # 启动接收和发送线程
            threading.Thread(target=self.receive_data, daemon=True).start()
            threading.Thread(target=self.send_data, daemon=True).start()

        except Exception as e:
            self.log.error(f"服务器启动失败: {str(e)}")
            self.stop()

    def data_log_save(self, data: str, data_type:str):
        if isinstance(data, bytes):
            decoded_data = data.decode('utf-8')
        else:
            decoded_data = data
        # 添加时间戳
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_saved = f"[{timestamp}][{self.name}][{data_type}]: {decoded_data}"
        
        # 将数据写入文件
        with open(f"src/chemistry_os/src/log/connect_{self.file_timestape}.log", "a", encoding="utf-8") as file:
            file.write(f"{data_saved}\n")

    def data_normal_save(self, data: str, end_str: str = ""):
        if isinstance(data, bytes):
            decoded_data = data.decode('utf-8')
        else:
            decoded_data = data
        # 将数据写入文件
        with open(f"src/chemistry_os/src/log/data_{self.file_timestape}.log", "a", encoding="utf-8") as file:
            file.write(f"{decoded_data}{end_str}")

    def receive_data(self):
        """
        接收客户端数据并存储到接收缓冲区。
        """
        while self.is_running:
            if self.is_connected:
                try:
                    # 检查 rx_buffer 是否已满
                    if len(self.rx_buffer) >= self.buffer_size:
                        self.log.warning("接收缓冲区已满，停止接收新数据")
                        time.sleep(0.5)  # 防止过度占用 CPU
                        continue

                    data = self.client_socket.recv(self.buffer_size)
                    if data:
                        self.rx_buffer.append(data.decode('utf-8'))
                        self.data_log_save(data,"receive")

                except Exception as e:
                    self.log.error(f"接收数据失败: {str(e)}")
                    self.disconnect_client()
            time.sleep(0.001)
        self.log.info("接收线程已停止")

    def send_data(self):
        """
        处理发送缓冲区中的数据。
        """
        while self.is_running:
            # 尝试接受客户端连接
            if not self.is_connected:
                try:
                    self.client_socket, self.client_address = self.server_socket.accept()
                    self.is_connected = True
                    self.log.info(f"客户端已连接: {self.client_address}")
                except Exception as e:
                    self.log.error(f"接受连接时发生错误: {str(e)}")

            if self.is_connected:
                self.package_data()  # 生成数据包并存储到发送缓冲区

            # 处理发送缓冲区中的数据
            if self.tx_buffer and self.is_connected:
                try:
                    data = self.tx_buffer.pop(0)
                    self.data_log_save(data,"send")
                    self.data_normal_save(data, end_str="\n")  # 保存数据到文件
                    self.client_socket.sendall(data.encode('utf-8'))
                    # self.log.info(f"发送数据: {data}")
                except Exception as e:
                    self.log.error(f"发送数据失败: {str(e)}")
                    self.disconnect_client()
            time.sleep(self.loop_time)  # 控制发送频率
        self.log.info("发送线程已停止")



    def package_data(self,end_str: str = ""):
        """
        根据注册的单元生成数据包并存储到发送缓冲区。
        
        :param units: 包含单元信息的列表，每个单元格式为：
                    ["name", 周期计数, 最大计数, 数据字典指针]
        """

        try:
            # 初始化数据包
            # packet = {
            #     "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),  # 当前时间戳
            #     "packet_id": self.pkg_ID,  # 包编号，递增
            #     "configs": {
            #         "requires_response": True,  # 是否需要回应
            #         "max_wait_time": 30,  # 最大等待时间
            #         "retry_attempts": 3  # 最大重试次数
            #     },
            #     "data": {}  # 数据内容
            # }
            packet = {}
            #     "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),  # 当前时间戳
            #     "packet_id": self.pkg_ID,  # 包编号，递增
            #     "configs": {
            #         "requires_response": True,  # 是否需要回应
            #         "max_wait_time": 30,  # 最大等待时间
            #         "retry_attempts": 3  # 最大重试次数
            #     },
            #     "data": {}  # 数据内容
            # }

            # 标记是否有数据单元达到响应条件
            has_response = False

            # 遍历注册的单元，生成数据内容
            for unit in TCPServer.data_units:
                name, cycle_count, max_count, data_dict,func = unit

                if cycle_count[0] >= max_count:

                    cycle_count[0] = 0  # 到达最大计数时置零
                    # packet["data"][name] = data_dict  # 添加数据到包中
                    func()  # 调用函数获取最新数据
                    packet = data_dict  # 添加数据到包中
                    has_response = True  # 至少有一个单元达到响应条件
                else:
                    cycle_count[0] += 1


            if has_response:
                self.tx_buffer.append(json.dumps(packet))
                if end_str:  # 如果提供了结束符，则添加到发送缓冲区
                    self.tx_buffer.append(end_str)  # 添加结束符到发送缓冲区
                self.pkg_ID += 1  # 包编号递增
                # self.log.info(f"数据包已生成并存储到发送缓冲区: {packet}")
        except Exception as e:
            self.log.error(f"生成数据包失败: {str(e)}")

    def register(self, name: str, max_cycle: int, data_dict: Dict[str, Any],func: Callable[[], None] =  None):
        """
        注册一个数据单元到 data_units 中。
        
        :param name: 数据单元名称
        :param max_cycle: 最大周期计数
        :param data_dict: 数据字典，包含数据内容
        """
        try:
            # 检查是否已存在相同名称的单元
            for unit in TCPServer.data_units:
                if unit[0] == name:
                    self.log.warning(f"数据单元 '{name}' 已存在，跳过注册")
                    return

            # 初始化周期计数为 0
            cycle_count = [0]
            # 创建数据单元
            if func is None:
                func = lambda: None  # 如果未提供函数，则使用空函数
            data_unit = [name, cycle_count, max_cycle, data_dict, func]
            # 将数据单元添加到 data_units 列表
            TCPServer.data_units.append(data_unit)
            self.log.info(f"数据单元已注册: {data_unit}")
        except Exception as e:
            self.log.error(f"注册数据单元失败: {str(e)}")

    def send(self, data: Union[str, Dict[str, Any]]):
        """
        发送数据到客户端。
        """
        if not self.is_connected:
            self.log.warning("没有连接的客户端，无法发送数据")
            return
        if isinstance(data, dict):
            data = json.dumps(data)
        self.tx_buffer.append(data)

    def set_data_callback(self, callback: Callable[[str], None]):
        """
        设置接收到数据时的回调函数。
        """
        self.callback = callback

    def disconnect_client(self):
        """
        断开客户端连接。
        """
        self.is_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
        self.client_socket = None
        self.client_address = None

    def stop(self):
        """
        停止服务器。
        """
        self.is_running = False
        self.disconnect_client()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        self.log.info("服务器已停止")