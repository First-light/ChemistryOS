import socket
import json
import time
import threading

class TCPClient:
    """
    简单的TCP客户端，用于测试与服务端的通信
    """
    _instance = None
    _lock = threading.Lock()


    def __new__(cls, host='localhost', port=8888, buffer_size=4096):
        """
        创建单例实例
        
        Args:
            host: 服务器主机地址，默认为'localhost'
            port: 服务器端口，默认为8888
            buffer_size: 接收数据的缓冲区大小，默认为4096字节
        """
        with cls._lock:  # 确保线程安全
            if cls._instance is None:
                # 创建新实例
                cls._instance = super().__new__(cls)
                # 初始化实例
                cls._instance.__init__(host, port, buffer_size)
        return cls._instance
    
    def __init__(self, host='localhost', port=8888, buffer_size=4096):
        """
        初始化TCP客户端
        
        Args:
            host: 服务器主机地址，默认为'localhost'
            port: 服务器端口，默认为8888
            buffer_size: 接收数据的缓冲区大小，默认为4096字节
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
        self._is_connected = False
        self._is_running = False
        self._listen_thread = None
    
    def connect(self):
        """
        连接到服务器
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self._is_connected = True
            self._is_running = True
            
            # 启动监听线程
            self._listen_thread = threading.Thread(target=self._listen_for_data, daemon=True)
            self._listen_thread.start()
            
            print(f"已连接到服务器: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"连接服务器失败: {str(e)}")
            return False
    
    def _listen_for_data(self):
        """
        在后台线程中监听服务器数据
        """
        while self._is_running and self._is_connected:
            try:
                data = self.socket.recv(self.buffer_size)
                if not data:
                    print("服务器已断开连接")
                    self._is_connected = False
                    break
                
                try:
                    # 尝试解析为JSON
                    json_data = json.loads(data.decode('utf-8'))
                    print(f"收到服务器JSON数据: {json_data}")
                    
                    # 处理服务器的心跳消息
                    if isinstance(json_data, dict) and json_data.get('type') == 'heartbeat':
                        print(f"收到服务器心跳，计数器: {json_data.get('counter')}")
                        
                except json.JSONDecodeError:
                    # 如果不是JSON，则以原始数据形式处理
                    print(f"收到服务器原始数据: {data}")
                    
            except ConnectionResetError:
                print("连接被服务器重置")
                self._is_connected = False
                break
            except Exception as e:
                print(f"接收数据时发生错误: {str(e)}")
                self._is_connected = False
                break
    
    def send_json(self, data):
        """
        向服务器发送JSON数据
        
        Args:
            data: 要发送的JSON数据
            
        Returns:
            bool: 发送是否成功
        """
        if not self._is_connected:
            print("未连接到服务器，无法发送数据")
            return False
        
        try:
            json_str = json.dumps(data)
            self.socket.sendall(json_str.encode('utf-8'))
            print(f"已发送JSON数据: {data}")
            return True
        except Exception as e:
            print(f"发送数据失败: {str(e)}")
            self._is_connected = False
            return False
    
    def close(self):
        """
        关闭连接
        """
        self._is_running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            
        self._is_connected = False
        
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2.0)
            
        print("已关闭连接")
    
    def is_connected(self):
        """
        检查是否已连接到服务器
        
        Returns:
            bool: 是否已连接
        """
        return self._is_connected

if __name__ == "__main__":
    # 创建客户端实例
    client = TCPClient(host='localhost', port=8888)
    
    # 连接到服务器
    if not client.connect():
        print("无法连接到服务器，程序退出")
        exit(1)
    
    try:
        # 发送一个ping消息
        client.send_json({'message': 'ping'})
        
        # 主循环
        counter = 0
        while client.is_connected():
            # 每隔10秒发送一条消息
            if counter % 10 == 0:
                client.send_json({
                    'message': f'客户端消息 #{counter//10}',
                    'timestamp': time.time()
                })
            
            counter += 1
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在关闭客户端...")
    finally:
        client.close() 