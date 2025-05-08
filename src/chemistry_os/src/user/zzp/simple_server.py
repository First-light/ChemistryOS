import sys
import os
import time

# 将包所在路径添加到sys.path，这样可以直接运行示例而不需要安装包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tcp_server.server import TCPServer

def handle_client_data(data):
    """处理从客户端接收到的数据"""
    print(f"收到客户端数据: {data}")
    
    # 如果接收到的是字典，并且包含'message'键
    if isinstance(data, dict) and 'message' in data:
        # 可以根据收到的消息做相应处理
        if data['message'] == 'ping':
            # 发送回复
            server.send_json({'message': 'pong', 'timestamp': time.time()})
    
    # 如果是其他类型的数据，可以添加其他处理逻辑

if __name__ == "__main__":
    # 创建TCP服务端实例
    server = TCPServer(host='0.0.0.0', port=8888, buffer_size=4096)
    
    # 设置数据回调函数
    server.set_data_callback(handle_client_data)
    
    # 启动服务器
    print("启动TCP服务器，等待客户端连接...")
    server.start()
    
    try:
        # 主程序可以继续运行
        counter = 0
        while True:
            # 每隔5秒发送一次消息（如果有客户端连接）
            if counter % 5 == 0:
                if server.is_connected():
                    print(f"发送消息到客户端: {counter}")
                    server.send_json({
                        'type': 'heartbeat',
                        'counter': counter,
                        'timestamp': time.time()
                    })
                else:
                    print("等待客户端连接...")
            
            counter += 1
            time.sleep(1)
            
    except KeyboardInterrupt:
        # 捕获Ctrl+C，优雅地关闭服务器
        print("\n正在关闭服务器...")
        server.stop()
        print("服务器已关闭。") 