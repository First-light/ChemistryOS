import sys


sys.path.append('src/chemistry_os/src')
import shlex
import threading
import time
from facility import Facility
from structs import BufferMod, ParserState
from utilities.utility_param import ParamUtils
from utilities.utility_log import LogUtils

class CommandParser(Facility):
    
    """
    CommandParser is responsible for parsing command lines and executing the corresponding commands
    on the facilities.
    """
    using_unity = False
    unity_buffer = []
    unity_flag = BufferMod.NONE
    type = "parser"
    

    def __init__(self,name = "parser",parse_only=False):
        super().__init__(name, type = CommandParser.type, skip_append=parse_only)
        self.parser_thread = None
        self.execute_thread = None
        self.parser_buffer:list[str] = []
        self.execute_buffer:list[str] = []
        self.input_thread_shell = None
        self.input_thread_curses = None
        self.input_thread_unity = None
        self.running = False
        self.is_executing = False
        self.init_dict = ParamUtils.get_init_params(self)
        self.parser_state:ParserState = ParserState.READY
        self._last_input = ""  # 存储最后的输入

    def start(self, input="shell"):

        if self.running == False:
            self.log.info("开启指令解析")
            self.running = True
            self.parser_thread = threading.Thread(target=self.parser_thread_func)
            self.parser_thread.daemon = True
            self.parser_thread.start()
            self.execute_thread = threading.Thread(target=self.execute_thread_func)
            self.execute_thread.daemon = True
            self.execute_thread.start()

        if input == "shell" :
            self.log.info("开启命令行输入")
            self.input_thread_shell = threading.Thread(target=self.shell_input)
            self.input_thread_shell.daemon = True
            self.input_thread_shell.start()
        elif input == "curses":
            self.log.info("开启curses输入")
            self.input_thread_curses = threading.Thread(target=self.curses_input)
            self.input_thread_curses.daemon = True
            self.input_thread_curses.start()
        elif input == "unity":
            self.log.info("开启unity远程输入")
            self.input_thread_unity = threading.Thread(target=self.unity_input)
            self.input_thread_unity.daemon = True
            self.input_thread_unity.start()
        elif input == "none":
            pass
        else:
            self.log.warning(f"未知输入模式: {input}")

    def end(self):
        self.running = False
        # 清理 curses 界面
        if hasattr(self, '_using_curses') and self._using_curses:
            from lib.curses.simple import cleanup_curses_ui
            cleanup_curses_ui()
        
        if self.parser_thread:
            self.parser_thread.join()
        if self.input_thread_shell:
            self.input_thread_shell.join()

    def execute_thread_func(self):
        while self.running:
            if self.execute_buffer:
                self.is_executing = True
                command_line_t = self.execute_buffer.pop(0)
                self.parse(command_line_t)
                self.is_executing = False
            time.sleep(0.002)
        self.log.info("执行器线程退出")

    def parser_thread_func(self):
        while self.running:
            if self.parser_buffer:
                # 将比特流转换为字符串
                command_line_t = self.parser_buffer.pop(0)  # 改为 pop(0) 获取第一个完整命令
                self._last_input = command_line_t
                # 调用命令解析器
                if self.parser_state is ParserState.READY:
                    if not self.is_executing: self.execute_buffer.append(command_line_t)
                elif self.parser_state is ParserState.INPUT_WAIT:
                    self.parser_state = ParserState.READY
                else:
                    pass
            time.sleep(0.002)  # 模拟读取间隔
        self.log.info("解析器线程退出")

    def cmd_init(self):

        pass

    def shell_input(self):
        while self.running:
            user_input = input(">")
            self.parser_buffer.append(user_input)  # 改为 append，保持完整命令
            time.sleep(0.01)

    def curses_input(self):#不算好用
        """使用新的极简 curses 界面"""
        self._using_curses = True
        from lib.curses.simple import curses_input_for_parser
        curses_input_for_parser(self)

    def unity_input(self):
        """unity输入"""
        CommandParser.using_unity = True
        while self.running:
            if CommandParser.unity_flag == BufferMod.READY:
                self.parser_buffer.append(''.join(CommandParser.unity_buffer))
                CommandParser.unity_buffer.clear()
                CommandParser.unity_flag = BufferMod.NONE
            time.sleep(0.01)

    @staticmethod
    def wait_input(name:str,tips:str = "请输入任意内容继续...") -> str:
        facility_parser = Facility.get_facility_by_name(name)
        input_data:str = ""
        if facility_parser and isinstance(facility_parser, CommandParser) and facility_parser.running is True:
            facility_parser.log.info(tips)
            facility_parser.parser_state = ParserState.INPUT_WAIT
            while facility_parser.parser_state == ParserState.INPUT_WAIT:
                time.sleep(0.01)
            input_data = facility_parser._last_input
        elif facility_parser is None:
            LogUtils.log.warning(f"未找到名为 {name} 的解析器")
        elif not isinstance(facility_parser, CommandParser):
            LogUtils.log.warning(f"名为 {name} 的解析器不是 CommandParser 类型")
        elif facility_parser.running is False:
            LogUtils.log.warning(f"名为 {name} 的解析器未运行，无法等待输入")
        else:
            pass
            
        return input_data


    def parse(self, command_line:str) -> bool:
        # 使用简单的空格分割，只分割第一个空格
        parts = command_line.strip().split(' ', 1)
        if len(parts) < 1:
            return True
        
        objectname = parts[0]
        command = parts[1] if len(parts) > 1 else ""  # 保留原始的命令字符串，包括双引号
        
        facility_t = Facility.get_facility_by_name(objectname)
        if facility_t is None:
            self.log.warning(f"未知设备:{objectname}")
            return False
        else:
            ret:bool = facility_t.parser.cmd(command)
            return ret
        
    def cmd_error_handing(self):
        pass

    def cmd_stop_handing(self):
        pass

    def cmd_reset(self):#从error/stop恢复idle的状态
        pass





