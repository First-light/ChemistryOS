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

    def cmd_init(self):
        pass

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
                        decoded_data = data.decode('utf-8')
                        self.rx_buffer.append(decoded_data)
                        # 添加时间戳
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data_saved = f"[{timestamp}][{self.name}][receive]: {decoded_data}"
                        
                        # 将数据写入文件
                        with open("src/chemistry_os/src/log/data.log", "a", encoding="utf-8") as file:
                            file.write(f"{data_saved}\n")
                        
                        if self.callback:
                            self.callback(decoded_data)

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
            try:
                self.client_socket, self.client_address = self.server_socket.accept()
                self.is_connected = True
                self.log.info(f"客户端已连接: {self.client_address}")
            except Exception as e:
                self.log.error(f"接受连接时发生错误: {str(e)}")

            # 处理发送缓冲区中的数据
            if self.tx_buffer and self.is_connected:
                try:
                    data = self.tx_buffer.pop(0)
                    self.client_socket.sendall(data.encode('utf-8'))
                    self.log.info(f"发送数据: {data}")
                except Exception as e:
                    self.log.error(f"发送数据失败: {str(e)}")
                    self.disconnect_client()
            time.sleep(0.001)
        self.log.info("发送线程已停止")

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