import logging
import queue
import sys
import threading
import time
from collections import deque

# --- ANSI 转义码常量 ---
# 将光标移动到屏幕左下角 (假设一个足够大的行号)
MOVE_TO_BOTTOM_LEFT = "\033[999;1H" 
# 清除从光标到行尾的内容
CLEAR_LINE = "\033[K"
# 保存光标位置
SAVE_CURSOR = "\033[s"
# 恢复光标位置
RESTORE_CURSOR = "\033[u"
# 向上滚动一行
SCROLL_UP = "\n"

class AnsiUI:
    """
    一个使用ANSI转义码实现的轻量级终端UI。
    它提供一个滚动的日志区域和一个固定的底部输入行。
    """
    def __init__(self, parser_instance):
        self.parser_instance = parser_instance
        self.log_queue = queue.Queue()
        self.input_buffer = ""
        self.prompt = "> "
        self.screen_lock = threading.Lock()
        self._is_running = False
        self.log_history = deque(maxlen=200) # 保存最近的日志

    def _configure_logging(self):
        """配置根logger，将日志重定向到内部队列。"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 清理现有处理器，避免重复输出
        if root_logger.hasHandlers():
            root_logger.handlers.clear()
            
        # 自定义处理器，将日志记录放入队列
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            def emit(self, record):
                self.log_queue.put(self.format(record))

        handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    def _redraw_input_line(self):
        """在屏幕底部重绘输入行。"""
        with self.screen_lock:
            sys.stdout.write(SAVE_CURSOR)
            # 移动到左下角并清除该行
            sys.stdout.write(MOVE_TO_BOTTOM_LEFT + CLEAR_LINE)
            # 打印提示符和输入缓冲
            sys.stdout.write(self.prompt + self.input_buffer)
            sys.stdout.write(RESTORE_CURSOR)
            sys.stdout.flush()

    def _handle_log_messages(self):
        """处理并打印队列中的日志消息。"""
        logs_to_print = []
        while not self.log_queue.empty():
            logs_to_print.append(self.log_queue.get_nowait())

        if logs_to_print:
            with self.screen_lock:
                sys.stdout.write(SAVE_CURSOR)
                # 移动到输入行的上一行
                sys.stdout.write(MOVE_TO_BOTTOM_LEFT + "\033[A")
                
                # 打印所有新日志，每条日志后都换行
                for msg in logs_to_print:
                    sys.stdout.write(SCROLL_UP + CLEAR_LINE + msg)
                    self.log_history.append(msg)

                # 恢复光标到输入行
                sys.stdout.write(RESTORE_CURSOR)
                sys.stdout.flush()
            
            # 打印完日志后，重绘输入行以确保它在最底部
            self._redraw_input_line()

    def _input_thread_func(self):
        """一个独立的线程，用于读取标准输入。"""
        # 这是一个简化的实现，更健壮的实现需要使用 termios 等库
        # 来实现真正的非阻塞、逐字符读取。
        # 这里的 input() 是阻塞的，但可以用于演示。
        while self._is_running:
            try:
                user_input = input() # 这是阻塞的
                with self.screen_lock:
                    self.parser_instance.parser_buffer.append(user_input)
                    self.log_history.append(self.prompt + user_input)
                    self.input_buffer = "" # 清空缓冲区
                self._redraw_input_line()
            except (EOFError, KeyboardInterrupt):
                self._is_running = False
                break

    def start(self):
        """启动UI的主循环和输入线程。"""
        self._is_running = True
        self._configure_logging()

        # 清屏并准备输入区
        sys.stdout.write("\033[2J\033[H") # 清屏并移动到左上角
        sys.stdout.write("\n" * 20) # 滚动一些空间
        self._redraw_input_line()

        # 启动一个简化的输入线程
        # 注意：Python的input()会阻塞，这使得日志和输入交错变得困难。
        # 一个更高级的实现会用termios来逐字符读取。
        # 为了演示，我们让日志打印和input()调用在一个循环里。
        
        print("ANSI UI 已启动。在下方输入命令。")

        while self._is_running:
            self._handle_log_messages()
            
            # 检查是否有用户输入（这是一个简化的轮询方式）
            # 理想情况下，输入应该在另一个线程中处理
            # 这里我们用一个简单的input()来演示
            try:
                # 这是一个简化的例子，实际应用中input()会阻塞所有事情
                # 真实场景需要一个非阻塞的输入读取器
                # 此处我们用一个超时来模拟
                # 由于标准库没有好的跨平台非阻塞输入，我们保持简单
                time.sleep(0.1)

            except (KeyboardInterrupt, EOFError):
                self.stop()
    
    def stop(self):
        """停止UI。"""
        self._is_running = False
        print("\nANSI UI 正在关闭...")

def start_ansi_ui(parser_instance):
    """
    为 CommandParser 启动并管理一个 ANSI UI 界面。
    """
    ui = AnsiUI(parser_instance)
    # 因为input()是阻塞的，所以在一个新线程中运行UI主循环
    ui_thread = threading.Thread(target=ui.start, daemon=True)
    ui_thread.start()
    
    # 启动一个单独的线程来处理阻塞的input()
    input_thread = threading.Thread(target=ui._input_thread_func, daemon=True)
    input_thread.start()

    # 让主线程等待，直到UI线程结束（例如通过Ctrl+C）
    while ui._is_running:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            ui.stop()
            break
