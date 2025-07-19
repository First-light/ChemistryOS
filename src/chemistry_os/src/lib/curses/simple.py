"""
ChemistryOS 极简版 Curses UI
只包含输出区和输入区，动态适应终端大小
"""
import curses
import threading
import time
import logging
from datetime import datetime


class SimpleCursesUI:
    """极简的 Curses 用户界面 - 只有输出区和输入区"""
    
    def __init__(self):
        self.stdscr = None
        self.running = False
        self.output_win = None
        self.input_win = None
        self.command_history = []
        self.history_index = 0
        self.current_input = ""
        self.cursor_pos = 0
        self.output_buffer = []
        self.max_output_lines = 1000
        self.log_handler = None
        self.terminal_height = 0
        self.terminal_width = 0
        
    def initialize(self):
        """初始化 curses 环境"""
        try:
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(1)
            self.stdscr.keypad(True)
            self.stdscr.timeout(100)  # 设置超时避免阻塞
            
            # 设置颜色
            if curses.has_colors():
                curses.start_color()
                curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # 输入提示
                curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)    # 日志信息
            
            self.setup_windows()
            self.setup_logging()
            self.running = True
            return True
            
        except Exception as e:
            self.cleanup()
            raise e
    
    def setup_windows(self):
        """根据终端大小设置窗口 - 只有输出区和输入区"""
        height, width = self.stdscr.getmaxyx()
        self.terminal_height = height
        self.terminal_width = width
        
        # 输出区：占用除了最后一行外的所有空间
        output_height = height - 1
        self.output_win = curses.newwin(output_height, width, 0, 0)
        self.output_win.scrollok(True)
        
        # 输入区：只占用最后一行
        self.input_win = curses.newwin(1, width, height - 1, 0)
        
        self.refresh_all()
    
    def setup_logging(self):
        """设置日志处理器，将日志重定向到 curses 输出"""
        class CursesLogHandler(logging.Handler):
            def __init__(self, ui):
                super().__init__()
                self.ui = ui
                
            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.ui.add_output(f"[LOG] {msg}")
                except Exception:
                    pass
        
        # 创建日志处理器
        self.log_handler = CursesLogHandler(self)
        self.log_handler.setFormatter(logging.Formatter(
            '[%(name)s] [%(levelname)s]: %(message)s'
        ))
        
        # 添加到根日志器
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)
    
    def cleanup(self):
        """清理 curses 环境"""
        self.running = False
        
        # 移除日志处理器
        if self.log_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)
        
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
    
    def add_output(self, text):
        """添加输出到显示区域"""
        if not text:
            return
            
        lines = str(text).split('\n')
        for line in lines:
            if line.strip():  # 忽略空行
                timestamp = datetime.now().strftime('%H:%M:%S')
                formatted_line = f"[{timestamp}] {line}"
                self.output_buffer.append(formatted_line)
        
        # 限制缓冲区大小
        if len(self.output_buffer) > self.max_output_lines:
            self.output_buffer = self.output_buffer[-self.max_output_lines:]
        
        self.refresh_output()
    
    def refresh_output(self):
        """刷新输出窗口"""
        if not self.output_win:
            return
            
        try:
            self.output_win.clear()
            height, width = self.output_win.getmaxyx()
            
            # 显示最后的输出行
            start_line = max(0, len(self.output_buffer) - height)
            for i, line in enumerate(self.output_buffer[start_line:]):
                if i >= height:
                    break
                    
                # 处理过长的行
                display_line = line
                if len(line) > width - 1:
                    display_line = line[:width - 4] + "..."
                
                try:
                    if "[LOG]" in line and curses.has_colors():
                        self.output_win.addstr(i, 0, display_line, curses.color_pair(2))
                    else:
                        self.output_win.addstr(i, 0, display_line)
                except curses.error:
                    pass
            
            self.output_win.refresh()
        except curses.error:
            pass
    
    def refresh_input(self):
        """刷新输入窗口"""
        if not self.input_win:
            return
            
        try:
            self.input_win.clear()
            height, width = self.input_win.getmaxyx()
            
            prompt = "> "
            display_text = prompt + self.current_input
            
            # 处理过长的输入 - 滚动显示
            if len(display_text) > width - 1:
                start_pos = max(0, len(prompt) + self.cursor_pos - width + 5)
                display_text = display_text[start_pos:]
                cursor_x = len(display_text) - len(self.current_input) + self.cursor_pos - start_pos
            else:
                cursor_x = len(prompt) + self.cursor_pos
            
            # 显示提示和输入
            if curses.has_colors():
                self.input_win.addstr(0, 0, display_text, curses.color_pair(1))
            else:
                self.input_win.addstr(0, 0, display_text)
            
            # 设置光标位置
            cursor_x = max(0, min(cursor_x, width - 1))
            try:
                self.input_win.move(0, cursor_x)
            except curses.error:
                pass
            self.input_win.refresh()
        except curses.error:
            pass
    
    def check_resize(self):
        """检查终端大小变化并重新设置窗口"""
        try:
            height, width = self.stdscr.getmaxyx()
            if height != self.terminal_height or width != self.terminal_width:
                self.terminal_height = height
                self.terminal_width = width
                
                # 重新创建窗口
                self.setup_windows()
                return True
        except curses.error:
            pass
        return False
    
    def refresh_all(self):
        """刷新所有窗口"""
        self.check_resize()
        self.refresh_output()
        self.refresh_input()
    
    def handle_input(self, parser_instance):
        """处理用户输入"""
        self.add_output("ChemistryOS 极简模式已启动")
        self.add_output("使用 ↑↓ 键浏览命令历史，Ctrl+C 退出")
        
        while self.running and parser_instance.running:
            try:
                self.refresh_all()
                
                # 获取按键 (非阻塞)
                key = self.stdscr.getch()
                
                if key == -1:  # 无输入，继续循环
                    time.sleep(0.01)
                    continue
                
                # 忽略鼠标滚轮事件，避免递归错误
                if key == curses.KEY_MOUSE:
                    continue
                
                if key == ord('\n') or key == ord('\r'):  # 回车
                    if self.current_input.strip():
                        # 添加到历史
                        if not self.command_history or self.command_history[-1] != self.current_input:
                            self.command_history.append(self.current_input)
                        
                        # 显示执行的命令
                        self.add_output(f"> {self.current_input}")
                        
                        # 发送到解析器
                        parser_instance.buffer.extend(self.current_input)
                        
                        # 清空输入
                        self.current_input = ""
                        self.cursor_pos = 0
                        self.history_index = len(self.command_history)
                
                elif key == curses.KEY_UP:  # 上箭头
                    if self.history_index > 0:
                        self.history_index -= 1
                        self.current_input = self.command_history[self.history_index]
                        self.cursor_pos = len(self.current_input)
                
                elif key == curses.KEY_DOWN:  # 下箭头
                    if self.history_index < len(self.command_history) - 1:
                        self.history_index += 1
                        self.current_input = self.command_history[self.history_index]
                        self.cursor_pos = len(self.current_input)
                    elif self.history_index == len(self.command_history) - 1:
                        self.history_index = len(self.command_history)
                        self.current_input = ""
                        self.cursor_pos = 0
                
                elif key == curses.KEY_RIGHT:  # 右箭头
                    if self.cursor_pos < len(self.current_input):
                        self.cursor_pos += 1
                
                elif key == curses.KEY_LEFT:  # 左箭头
                    if self.cursor_pos > 0:
                        self.cursor_pos -= 1
                
                elif key == 127 or key == curses.KEY_BACKSPACE:  # 退格
                    if self.cursor_pos > 0:
                        self.current_input = (self.current_input[:self.cursor_pos-1] + 
                                            self.current_input[self.cursor_pos:])
                        self.cursor_pos -= 1
                
                elif key == curses.KEY_DC:  # Delete
                    if self.cursor_pos < len(self.current_input):
                        self.current_input = (self.current_input[:self.cursor_pos] + 
                                            self.current_input[self.cursor_pos+1:])
                
                elif key == 1:  # Ctrl+A (行首)
                    self.cursor_pos = 0
                
                elif key == 5:  # Ctrl+E (行尾)
                    self.cursor_pos = len(self.current_input)
                
                elif key == 21:  # Ctrl+U (清空行)
                    self.current_input = ""
                    self.cursor_pos = 0
                
                elif 32 <= key <= 126:  # 可打印字符
                    char = chr(key)
                    self.current_input = (self.current_input[:self.cursor_pos] + 
                                        char + self.current_input[self.cursor_pos:])
                    self.cursor_pos += 1
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                # 避免递归错误，简单忽略未知事件
                pass


# 全局实例
_curses_ui = None

def get_curses_ui():
    """获取全局 curses UI 实例"""
    global _curses_ui
    if _curses_ui is None:
        _curses_ui = SimpleCursesUI()
    return _curses_ui

def cleanup_curses_ui():
    """清理 curses UI"""
    global _curses_ui
    if _curses_ui:
        _curses_ui.cleanup()
        _curses_ui = None

def curses_input_for_parser(parser_instance):
    """为 CommandParser 提供的极简 curses 输入方法"""
    ui = get_curses_ui()
    try:
        if ui.initialize():
            ui.handle_input(parser_instance)
    except Exception as e:
        try:
            ui.add_output(f"Curses 错误: {e}")
        except:
            pass
    finally:
        cleanup_curses_ui()