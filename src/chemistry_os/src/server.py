import socket
import threading
import json
import logging
import time
from typing import Dict, Any, Callable, Optional, Union
from facility import Facility

class TCPServer(Facility):
    """
    TCP服务端类，提供连接、发送和接收数据的功能。
    """
    type = "tcp_server"
    def __init__(self, host: str = '0.0.0.0', port: int = 8888, buffer_size: int = 4096):
        """
        初始化TCP服务端
        """
        super().__init__(name=f"tcp:{host}:{port}", type = TCPServer.type)
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
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.is_running = True
            self.log.info(f"服务器启动成功，监听地址: {self.host}:{self.port}")

            threading.Thread(target=self._accept_connections, daemon=True).start()
            threading.Thread(target=self._process_tx_buffer, daemon=True).start()
        except Exception as e:
            self.log.error(f"服务器启动失败: {str(e)}")
            self.stop()

    def _accept_connections(self):
        """
        接受客户端连接。
        """
        while self.is_running:
            try:
                self.client_socket, self.client_address = self.server_socket.accept()
                self.is_connected = True
                self.log.info(f"客户端已连接: {self.client_address}")
                threading.Thread(target=self._receive_data, daemon=True).start()
            except Exception as e:
                self.log.error(f"接受连接时发生错误: {str(e)}")

    def _receive_data(self):
        """
        接收客户端数据并存储到接收缓冲区。
        """
        while self.is_connected:
            try:
                data = self.client_socket.recv(self.buffer_size)
                if data:
                    decoded_data = data.decode('utf-8')
                    self.rx_buffer.append(decoded_data)
                    self.log.info(f"接收到数据: {decoded_data}")
                    if self.callback:
                        self.callback(decoded_data)
                else:
                    self.log.warning("客户端断开连接")
                    self._disconnect_client()
            except Exception as e:
                self.log.error(f"接收数据失败: {str(e)}")
                self._disconnect_client()

    def _process_tx_buffer(self):
        """
        处理发送缓冲区中的数据。
        """
        while self.is_running:
            if self.tx_buffer and self.is_connected:
                try:
                    data = self.tx_buffer.pop(0)
                    self.client_socket.sendall(data.encode('utf-8'))
                    self.log.info(f"发送数据: {data}")
                except Exception as e:
                    self.log.error(f"发送数据失败: {str(e)}")
                    self._disconnect_client()
            time.sleep(0.1)

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

    def _disconnect_client(self):
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
        self._disconnect_client()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        self.log.info("服务器已停止")