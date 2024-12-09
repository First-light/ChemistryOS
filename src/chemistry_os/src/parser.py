import sys
sys.path.append('src/chemistry_os/src')
import shlex
import threading
import time
from facility import facility

class CommandParser:
    """
    CommandParser is responsible for parsing command lines and executing the corresponding commands
    on the facilities.
    """
    def __init__(self):
        self.buffer = []
        self.buffer_thread = None
        self.input_thread = None
        self.running = False

    def start(self, input_mode="shell"):
        self.running = True
        self.buffer_thread = threading.Thread(target=self.parse_buffer)
        self.buffer_thread.daemon = True
        self.buffer_thread.start()

        if input_mode == "shell":
            self.input_thread = threading.Thread(target=self.shell_input)
            self.input_thread.daemon = True
            self.input_thread.start()
        else:
            raise ValueError(f"Unknown input mode: {input_mode}")

    def end(self):
        self.running = False
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
            time.sleep(1)  # 模拟读取间隔

    def shell_input(self):
        while self.running:
            user_input = input(">")
            self.buffer.extend(user_input)
            time.sleep(1)

    def parse(self, command_line):
        tokens = shlex.split(command_line)
        if len(tokens) < 1:#检查是否有输入，如果没有则直接忽略
            return

        objectname = tokens[0]
        command = " ".join(tokens[1:])  # 将命令和参数列表转换为字符串
        matched_CMD = None
        
        for tuple_t in facility.TupleList:
            name = tuple_t[0]
            cmd = tuple_t[1]
            if name == objectname:
                matched_CMD = cmd
                break

        if matched_CMD is None:
            print(f"Unknown facility: {objectname}")
            return
        else:
            matched_CMD(command)