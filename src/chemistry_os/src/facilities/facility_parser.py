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

    def __init__(self,name = "parser",skip_append=False):
        super().__init__(name, type = CommandParser.type, skip_append=skip_append)
        self.buffer = []
        self.buffer_thread = None
        self.input_thread_shell = None
        self.input_thread_curses = None
        self.input_thread_unity = None
        self.running = False
        self.init_dict = ParamUtils.get_init_params(self)
        self.parser_state:ParserState = ParserState.READY
        self._last_input = ""  # 存储最后的输入

    def start(self, input="shell"):

        if self.running == False:
            self.log.info("开启指令解析")
            self.running = True
            self.buffer_thread = threading.Thread(target=self.parser_thread)
            self.buffer_thread.daemon = True
            self.buffer_thread.start()

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
        
        if self.buffer_thread:
            self.buffer_thread.join()
        if self.input_thread_shell:
            self.input_thread_shell.join()

    def parser_thread(self):
        while self.running:
            if self.buffer:
                # 将比特流转换为字符串
                command_line = ''.join(self.buffer)
                self._last_input = command_line
                self.buffer.clear()
                # 调用命令解析器
                if self.parser_state is ParserState.READY:
                    self.parse(command_line)
                elif self.parser_state is ParserState.INPUT_WAIT:
                    self.parser_state = ParserState.READY
                else:
                    pass
            time.sleep(0.01)  # 模拟读取间隔

    def cmd_init(self):

        pass

    def shell_input(self):
        while self.running:
            user_input = input(">")
            self.buffer.extend(user_input)
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
                self.buffer.extend(CommandParser.unity_buffer)
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


    def parse(self, command_line) -> bool:
        tokens = shlex.split(command_line)
        if len(tokens) < 1:#检查是否有输入，如果没有则直接忽略
            return True

        objectname = tokens[0]
        command = " ".join(tokens[1:])  # 将命令和参数列表转换为字符串

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





