import threading

class Client:
    _instance = None
    _lock = threading.Lock()  # 用于线程安全

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
                cls._instance.host = host
                cls._instance.port = port
                cls._instance.buffer_size = buffer_size
                cls._instance.socket = None
                cls._instance._is_connected = False
                cls._instance._is_running = False
                cls._instance._listen_thread = None
                print(f"Client initialized with host={host}, port={port}, buffer_size={buffer_size}")
        return cls._instance

# 测试单例模式
if __name__ == "__main__":
    client1 = Client("192.168.1.1", 9999, 2048)
    client2 = Client("10.0.0.1", 8080, 1024)

    print(client1 is client2)  # 输出: True
    print(client1.host, client1.port, client1.buffer_size)  # 输出: 192.168.1.1 9999 2048
    print(client2.host, client2.port, client2.buffer_size)  # 输出: 192.168.1.1 9999 2048