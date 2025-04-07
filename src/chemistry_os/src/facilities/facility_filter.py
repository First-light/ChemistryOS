import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from structs import FacilityState
import serial
from serial.tools import list_ports
from time import sleep
import time
import serial

# sudo chmod 666 /dev/ttyUSB0 开串口权限

class Filter(Facility):
    type = "filter"

    def __init__(self, name: str, com: str, baudrate: int = 9600, address: int = 0x50 , sub_address: int = 0x00):
        """
        初始化抽滤装置类
        :param name: 设备名称
        :param com: 串口号
        :param baudrate: 波特率
        :param address: 主控地址，默认0x50
        """
        self.com = com
        self.baudrate = baudrate
        self.address = address
        self.sub_address = sub_address # 蠕动泵地址
        self.ser = None
        super().__init__(name, Filter.type)
        self.connect()

    def cmd_init(self):
        """
        注册指令
        """
        self.parser.register("test", self.test, {}, "send empty command")
        self.parser.register("pump", self.pump_control, {"address": self.sub_address, "state": 0}, "control pump on/off")
        self.parser.register("dir", self.set_pump_direction, {"address": self.sub_address, "direction": 0}, "set pump direction")
        self.parser.register("speed", self.set_pump_speed, {"address": self.sub_address, "speed": 0}, "set pump speed")
        self.parser.register("valve", self.valve_control, {"state": 0}, "control valve on/off")
        self.parser.register("airpump", self.air_pump_control, {"state": 0}, "control air pump on/off")
        self.parser.register("query", self.pump_query, {"address": self.sub_address}, "query pump status")
        self.parser.register("setaddr", self.set_pump_address, {"address": self.sub_address, "new_address": 0}, "set pump address")

    def cmd_error(self):
        self.cmd_print("error")

    def cmd_stop(self):
        self.cmd_print("stop")

    def connect(self):
        """
        连接设备
        """
        try:
            self.ser = serial.Serial(self.com, self.baudrate, timeout=1)
            self.cmd_print(f"{self.name} 成功连接到 {self.com}")
        except Exception as e:
            self.cmd_print(f"连接失败: {str(e)}")

    def set_pump_address(self, old_address: int, new_address: int):
        """
        设置蠕动泵的新地址
        :param address: 当前主控设备地址
        :param new_address: 新地址 (0x00 表示不设置新地址)
        """
        if new_address == 0:
            self.cmd_print("新地址无效，未进行设置")
            return

        command = [self.address, 0x04, old_address, 0x00, new_address, 0x55]
        response = self.send_command(command)

        # 如果设置成功，更新类中的 sub_address
        if response in response:
            self.sub_address = new_address
            self.cmd_print(f"蠕动泵地址已更新为: {hex(new_address)}")
        else:
            self.cmd_print("设置蠕动泵地址失败")

    def send_command(self, command: list):
        """
        发送指令到设备
        :param command: 指令列表
        """
        if not self.ser or not self.ser.is_open:
            self.cmd_print("设备未连接")
            return
        try:
            self.ser.write(bytearray(command))
            self.cmd_print(f"发送指令: {command}")
            sleep(0.1)
            response = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            self.cmd_print(f"设备响应: {response}")
            return response
        except Exception as e:
            self.cmd_print(f"发送指令失败: {str(e)}")

    def test(self):
        """
        空指令，用于回环测试
        """
        command = [self.address, 0x00, 0x55, 0x55, 0x55, 0x55]
        return self.send_command(command)

    def pump_control(self, address: int, state: int):
        """
        控制蠕动泵开关
        :param address: 蠕动泵设备地址
        :param state: 1=打开, 0=关闭
        """
        command = [self.address, 0x01, address, 0x00, state, 0x55]
        return self.send_command(command)

    def set_pump_direction(self, address: int, direction: int):
        """
        设置蠕动泵方向
        :param address: 蠕动泵设备地址
        :param direction: 方向，1=正转, 0=反转
        """
        command = [self.address, 0x02, address, 0x00, direction, 0x55]
        return self.send_command(command)

    def set_pump_speed(self, address: int, speed: int):
        """
        设置蠕动泵速度
        :param address: 蠕动泵设备地址
        :param speed: 速度值 (0-65535)
        """
        high_byte = (speed >> 8) & 0xFF
        low_byte = speed & 0xFF
        command = [self.address, 0x03, address, high_byte, low_byte, 0x55]
        return self.send_command(command)

    def valve_control(self, state: int):
        """
        控制三通阀门开关
        :param state: 1=打开, 0=关闭
        """
        command = [self.address, 0x05, state, 0x55, 0x55, 0x55]
        return self.send_command(command)

    def air_pump_control(self, state: int):
        """
        控制气泵开关
        :param state: 1=打开, 0=关闭
        """
        command = [self.address, 0x06, state, 0x55, 0x55, 0x55]
        return self.send_command(command)

    def pump_query(self, address: int):
        """
        查询蠕动泵开关、方向、速度
        :param address: 蠕动泵设备地址
        """
        command = [self.address, 0x09, address, 0x00, 0x00, 0x55]
        return self.send_command(command)