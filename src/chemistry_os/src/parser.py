import sys
sys.path.append('src/chemistry_os/src')
import shlex
from facilities.class_template import facility

class CommandParser:
    """
    CommandParser is responsible for parsing command lines and executing the corresponding commands
    on the facilities.
    """
    def __init__(self):
        pass

    def parse(self, command_line: str):
        """
        Parses the given command line and executes the corresponding command on the facility.

        将给定的命令行解析并分给指定设备对象的解析器进行处理。
        Args:
            command_line (str): The command line to parse and execute.
        """
        tokens = shlex.split(command_line)
        if len(tokens) < 1:
            return

        objectname = tokens[0]
        command = " ".join(tokens[1:])
        matched_CMD = None
        for name, cmd in facility.CMDlist:
            if name == objectname:
                matched_CMD = cmd
                break

        if matched_CMD is None:
            print(f"Unknown facility: {objectname}")
            return
        else:
            matched_CMD(command)
            
