import socket
import threading
import json
import logging
import time
from typing import Dict, Any, Callable, Optional, Union

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TCPServer')

class TCPServer:
    """
    TCP服务端类，提供异步等待连接、发送JSON数据和接收客户端数据的功能。
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8888, buffer_size: int = 1024):
        """
        初始化TCP服务端
        
        Args:
            host: 服务器主机地址，默认为'0.0.0.0'，表示接受所有网络接口的连接
            port: 服务器端口，默认为8888
            buffer_size: 接收数据的缓冲区大小，默认为1024字节
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self._is_running = False
        self._is_connected = False
        self._listen_thread = None
        self._accept_thread = None
        self._callback = None
        
    def start(self) -> None:
        """
        启动TCP服务端，开始监听连接
        """
        if self._is_running:
            logger.warning("服务器已经在运行中")
            return
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置端口复用，避免服务重启时出现端口被占用的问题
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self._is_running = True
            logger.info(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            
            # 在单独的线程中接受连接
            self._accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self._accept_thread.start()
        except Exception as e:
            logger.error(f"服务器启动失败: {str(e)}")
            self._cleanup()
            raise
    
    def _accept_connections(self) -> None:
        """
        在后台线程中接受客户端连接
        """
        logger.info("等待客户端连接...")
        
        while self._is_running:
            try:
                # 设置超时以便可以定期检查服务器是否仍在运行
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.client_socket = client_socket
                    self.client_address = client_address
                    self._is_connected = True
                    logger.info(f"客户端已连接: {client_address}")
                    
                    # 如果有回调函数，启动监听线程
                    if self._callback:
                        self._start_listen_thread()
                except socket.timeout:
                    continue
            except Exception as e:
                if self._is_running:  # 只有在正常运行时才记录错误
                    logger.error(f"接受连接时发生错误: {str(e)}")
                break
    
    def _start_listen_thread(self) -> None:
        """
        启动监听客户端数据的线程
        """
        if self._listen_thread and self._listen_thread.is_alive():
            return
            
        self._listen_thread = threading.Thread(target=self._listen_for_data, daemon=True)
        self._listen_thread.start()
    
    def _listen_for_data(self) -> None:
        """
        监听并处理来自客户端的数据
        """
        while self._is_connected and self._is_running:
            try:
                data = self.client_socket.recv(self.buffer_size)
                if not data:
                    logger.info("客户端已断开连接")
                    self._handle_client_disconnection()
                    break
                    
                try:
                    # 尝试解析为JSON
                    json_data = json.loads(data.decode('utf-8'))
                    if self._callback:
                        self._callback(json_data)
                except json.JSONDecodeError:
                    # 如果不是JSON，则以原始数据形式处理
                    if self._callback:
                        self._callback(data)
            except ConnectionResetError:
                logger.info("连接被客户端重置")
                self._handle_client_disconnection()
                break
            except Exception as e:
                logger.error(f"接收数据时发生错误: {str(e)}")
                self._handle_client_disconnection()
                break
    
    def _handle_client_disconnection(self) -> None:
        """
        处理客户端断开连接的情况
        """
        self._is_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.client_socket = None
        self.client_address = None
    
    def send_json(self, data: Dict[str, Any]) -> bool:
        """
        向客户端发送JSON数据
        
        Args:
            data: 要发送的JSON数据

        Returns:
            bool: 发送是否成功
        """
        if not self._is_connected or not self.client_socket:
            logger.warning("没有连接的客户端，无法发送数据")
            return False
            
        try:
            json_str = json.dumps(data)
            self.client_socket.sendall(json_str.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"发送数据失败: {str(e)}")
            self._handle_client_disconnection()
            return False
    
    def send_bytes(self, data: bytes) -> bool:
        """
        向客户端发送字节数据
        
        Args:
            data: 要发送的字节数据

        Returns:
            bool: 发送是否成功
        """
        if not self._is_connected or not self.client_socket:
            logger.warning("没有连接的客户端，无法发送数据")
            return False
            
        try:
            self.client_socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"发送数据失败: {str(e)}")
            self._handle_client_disconnection()
            return False
    
    def set_data_callback(self, callback: Callable[[Union[Dict[str, Any], bytes]], None]) -> None:
        """
        设置接收到客户端数据时的回调函数
        
        Args:
            callback: 回调函数，接收一个参数（解析后的JSON数据或原始字节数据）
        """
        self._callback = callback
        
        # 如果已经连接，则启动监听线程
        if self._is_connected and self.client_socket:
            self._start_listen_thread()
    
    def is_connected(self) -> bool:
        """
        检查是否有客户端连接
        
        Returns:
            bool: 是否有客户端连接
        """
        return self._is_connected
    
    def close_connection(self) -> None:
        """
        关闭当前客户端连接
        """
        if self._is_connected and self.client_socket:
            try:
                self.client_socket.close()
                logger.info("客户端连接已关闭")
            except Exception as e:
                logger.error(f"关闭客户端连接时发生错误: {str(e)}")
            finally:
                self._handle_client_disconnection()
    
    def stop(self) -> None:
        """
        停止服务器
        """
        if not self._is_running:
            return
            
        self._is_running = False
        
        # 关闭客户端连接
        if self._is_connected and self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # 等待线程结束
        if self._accept_thread and self._accept_thread.is_alive():
            self._accept_thread.join(timeout=2.0)
            
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2.0)
            
        logger.info("服务器已停止")
        self._cleanup()
    
    def _cleanup(self) -> None:
        """
        清理资源
        """
        self._is_running = False
        self._is_connected = False
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self._accept_thread = None
        self._listen_thread = None

    def __del__(self) -> None:
        """
        析构函数，确保资源被正确释放
        """
        self.stop() 