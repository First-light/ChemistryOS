import curses
import logging
import queue
import time
from collections import deque

# 全局变量，用于在主循环外控制curses
_stdscr = None
_is_running = False
_log_queue = queue.Queue() # 将队列提升为全局变量

class QueueHandler(logging.Handler):
    """
    一个将日志记录发送到队列的处理器，用于线程安全的日志记录。
    """
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        # 将格式化后的日志消息放入队列
        self.log_queue.put(self.format(record))

def configure_curses_logging():
    """
    在程序启动时配置日志系统，将日志重定向到全局队列。
    这个函数应该在任何可能产生日志的代码之前被调用。
    """
    global _log_queue
    root_logger = logging.getLogger()
    # 显式设置级别为INFO，以捕获所有INFO及以上级别的日志
    root_logger.setLevel(logging.INFO)

    # 清除根logger上所有现有的处理器，以防冲突
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 添加我们的队列处理器
    queue_handler = QueueHandler(_log_queue)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    queue_handler.setFormatter(formatter)
    root_logger.addHandler(queue_handler)
    
    # 返回队列的引用，虽然现在是全局的，但保持接口可能有用
    return _log_queue

def curses_input_for_parser(parser_instance):
    """
    为 CommandParser 启动并管理一个 curses UI 界面。
    
    这个函数会被 curses.wrapper 调用，以确保终端状态在
    程序退出或出错时能被正确恢复。
    
    :param parser_instance: CommandParser 的实例。
    """
    global _stdscr, _is_running, _log_queue
    
    def _main_loop(stdscr):
        """UI的主循环，由curses.wrapper调用"""
        global _stdscr, _is_running
        _stdscr = stdscr
        _is_running = True

        # --- 初始化 Curses ---
        curses.curs_set(1)  # 显示光标
        stdscr.nodelay(True)  # 非阻塞地获取输入
        stdscr.keypad(True)   # 启用特殊键（如箭头、F键）

        # --- 颜色对 (如果终端支持) ---
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1) # 输入文字颜色
            curses.init_pair(2, curses.COLOR_CYAN, -1)  # 边框颜色
            BORDER_COLOR = curses.color_pair(2)
        else:
            BORDER_COLOR = curses.A_NORMAL

        # --- 窗口布局 ---
        height, width = stdscr.getmaxyx()
        # 日志窗口高度为总高度减去输入区高度
        output_win_height = height - 3
        input_win_height = 3

        # 创建日志输出窗口
        output_win = curses.newwin(output_win_height, width, 0, 0)
        
        # 创建输入窗口的边框和窗口本身
        input_border_win = curses.newwin(input_win_height, width, output_win_height, 0)
        input_win = curses.newwin(1, width - 2, output_win_height + 1, 1)
        input_win.keypad(True)

        # --- 日志处理 ---
        # 使用固定大小的双端队列存储日志历史，以便滚动查看
        log_history = deque(maxlen=output_win_height * 5) 

        # --- 状态变量 ---
        input_buffer = ""
        
        # --- 主循环 ---
        while parser_instance.running and _is_running:
            # --- 绘制界面 ---
            # 绘制输入区边框和标题
            input_border_win.clear()
            input_border_win.box()
            input_border_win.addstr(0, 2, " Command Input ", BORDER_COLOR)
            input_border_win.refresh()

            # 从全局队列中获取所有新的日志消息
            while not _log_queue.empty():
                log_history.append(_log_queue.get_nowait())

            # 绘制日志窗口内容
            output_win.clear()
            # 计算开始绘制的日志行索引，以显示最新的日志
            start_index = max(0, len(log_history) - (output_win_height - 1))
            for i, line in enumerate(list(log_history)[start_index:]):
                # 截断过长的行以避免 curses 错误
                output_win.addstr(i, 1, line[:width-2])
            output_win.refresh()

            # --- 处理用户输入 ---
            input_win.clear()
            input_win.addstr(0, 0, input_buffer, curses.color_pair(1))
            input_win.refresh()

            try:
                # 从主屏幕获取输入，这样可以捕捉到功能键
                key = stdscr.getch() 
                if key != -1:
                    if key == curses.KEY_ENTER or key in [10, 13]:
                        if input_buffer:
                            # 将命令发送到解析器
                            parser_instance.parser_buffer.append(input_buffer)
                            log_history.append(f"> {input_buffer}") # 在日志中回显输入
                            input_buffer = ""
                    elif key == curses.KEY_BACKSPACE or key == 127:
                        input_buffer = input_buffer[:-1]
                    elif 32 <= key <= 126: # 只接受标准可打印字符
                        input_buffer += chr(key)
                    # 在此可以添加更多按键处理，如 KEY_UP/DOWN 实现历史记录功能
            except curses.error:
                # 忽略 getch 在窗口大小调整时可能引发的错误
                pass

            time.sleep(0.05) # 短暂休眠，降低CPU使用率

        # --- 清理 ---
        # 这里不再需要移除handler，因为它是全局配置的
        pass

    try:
        curses.wrapper(_main_loop)
    except Exception as e:
        logging.getLogger().error(f"Curses UI 异常退出: {e}")
    finally:
        _is_running = False

def cleanup_curses_ui():
    """
    一个外部可以调用的清理函数，用于确保curses在程序退出时被正确关闭。
    """
    global _is_running
    _is_running = False
    if _stdscr:
        _stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
