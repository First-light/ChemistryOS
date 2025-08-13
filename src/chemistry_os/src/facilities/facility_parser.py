import sys
sys.path.append('src/chemistry_os/src')
import shlex
import threading
import time
from facility import Facility
from structs import BufferMod
from utilities.utility_param import ParamUtils

class CommandParser(Facility):
    
    """
    CommandParser is responsible for parsing command lines and executing the corresponding commands
    on the facilities.
    """
    using_unity = False
    unity_buffer = []
    unity_flag = BufferMod.NONE
    type = "parser"

    def __init__(self,name = "parser"):
        super().__init__(name, type = CommandParser.type)
        self.buffer = []
        self.buffer_thread = None
        self.input_thread = None
        self.running = False
        self.init_dict = ParamUtils.get_init_params(self)

    def start(self, input="shell"):

        if self.running == False:
            self.log.info("开启指令解析")
            self.running = True
            self.buffer_thread = threading.Thread(target=self.parse_buffer)
            self.buffer_thread.daemon = True
            self.buffer_thread.start()

        if input == "shell":
            self.log.info("开启命令行输入")
            self.input_thread = threading.Thread(target=self.shell_input)
            self.input_thread.daemon = True
            self.input_thread.start()
        elif input == "curses":
            self.log.info("开启指令解析")
            self.input_thread = threading.Thread(target=self.curses_input)
            self.input_thread.daemon = True
            self.input_thread.start()
        elif input == "unity":
            self.log.info("开启远程输入")
            self.input_thread = threading.Thread(target=self.unity_input)
            self.input_thread.daemon = True
            self.input_thread.start()
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
        if self.input_thread:
            self.input_thread.join()

    def parse_buffer(self):
        while self.running:
            if self.buffer:
                # 将比特流转换为字符串
                command_line = ''.join(self.buffer)
                self.buffer.clear()
                # 调用命令解析器
                self.parse(command_line)
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

    def parse(self, command_line):
        tokens = shlex.split(command_line)
        if len(tokens) < 1:#检查是否有输入，如果没有则直接忽略
            return 0

        objectname = tokens[0]
        command = " ".join(tokens[1:])  # 将命令和参数列表转换为字符串

        facility_t = Facility.get_facility_by_name(objectname)
        if facility_t is None:
            self.log.warning(f"未知设备:{objectname}")
            return 1
        else:
            cmd = facility_t.parser.cmd
            ret = cmd(command)
            return ret





