import time
from time import sleep
from serial.tools import list_ports
import serial
from structs import FacilityState
from facility import Facility
import sys
sys.path.append('src/chemistry_os/src')

# sudo chmod 666 /dev/ttyUSB0 开串口权限
# ls -l /dev/ttyUSB* 查串口设备


class Filter(Facility):
    type = "filter"

    def __init__(self, name: str, com: str, baudrate: int = 9600, address: int = 0x50, sub_address: int = 0x01):
        """
        初始化抽滤装置类
        :param name: 设备名称
        :param com: 串口号

        :param baudrate: 波特率
        :param address: 主控地址，默认0x50
        """
        self.com = com
        self.ifconnect = False
        self.baudrate = baudrate
        self.address = address
        self.sub_address = sub_address  # 蠕动泵地址
        self.ser = None
        super().__init__(name, Filter.type)
        self.connect()

    def cmd_init(self):
        """
        注册指令
        """
        self.parser.register("test", self.test, {}, "send empty command")
        self.parser.register("pump", self.pump_control, {
                             "address": self.sub_address, "state": 0}, "control pump on/off")
        self.parser.register("dir", self.set_pump_direction, {
                             "address": self.sub_address, "direction": 0}, "set pump direction")
        self.parser.register("speed", self.set_pump_speed, {
                             "address": self.sub_address, "speed": 0}, "set pump speed")
        self.parser.register("valve", self.valve_control, {
                             "state": 0}, "control valve on/off")
        self.parser.register("airpump", self.air_pump_control, {
                             "state": 0}, "control air pump on/off")
        self.parser.register("query", self.pump_query, {
                             "address": self.sub_address}, "query pump status")
        self.parser.register("setaddr", self.set_pump_address, {
                             "address": self.sub_address, "new_address": 0}, "set pump address")


    def connect(self):
        """
        连接设备
        """
        try:
            self.ser = serial.Serial(self.com, self.baudrate, timeout=1)
            self.log.info(f"{self.name} 成功连接到 {self.com}")
            self.ifconnect = True
        except Exception as e:
            self.log.info(f"连接失败: {str(e)}")
            self.ifconnect = False


    def set_pump_address(self, old_address: int, new_address: int):
        """
        设置蠕动泵的新地址
        :param address: 当前主控设备地址
        :param new_address: 新地址 (0x00 表示不设置新地址)
        """
        if new_address == 0:
            self.log.info("新地址无效，未进行设置")
            return

        command = [self.address, 0x04, old_address, 0x00, new_address, 0x55]
        response = self.send_command(command)

        # 如果设置成功，更新类中的 sub_address
        if response in response:
            self.sub_address = new_address
            self.log.info(f"蠕动泵地址已更新为: {hex(new_address)}")
        else:
            self.log.info("设置蠕动泵地址失败")

    def send_command(self, command: list):
        """
        发送指令到设备
        :param command: 指令列表
        """
        if not self.ifconnect:
            self.log.info("设备未连接，请检查连接")
            return
    
        wait_time = 2.0
        command_t = bytearray(command)
        try:
            with serial.Serial(port=self.com, baudrate=self.baudrate, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command_t)
                self.log.info(f"发送指令: {command_t}")
                start_time = time.time()
                while True:
                    sleep(0.01)
                    if ser.in_waiting > 0:
                        # 读取设备响应
                        response = ser.read(ser.in_waiting)
                        response_str = response.decode('utf-8', errors='ignore')
                        self.log.info(f"设备响应: {response_str}")
                        return response_str
                    if time.time() - start_time > wait_time:
                        # 超过等待时间，认为超时
                        self.log.info("发送指令失败: 超时未收到响应")
                        return None

        except Exception as e:
            self.log.info(f"发送指令失败: {str(e)}")
            return None

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
        state_int = int(state)
        if state_int not in [0, 1]:
            self.log.info("无效的阀门状态，请输入 1 或 0")
            return
        state_byte = state_int.to_bytes(1, byteorder='big')
        command = [self.address, 0x01, address, 0x00, state_byte[0], 0x55]
        return self.send_command(command)

    def set_pump_direction(self, address: int, direction: int):
        """
        设置蠕动泵方向
        :param address: 蠕动泵设备地址
        :param direction: 方向，1=正转, 0=反转
        """
        direction_int = int(direction)
        if direction_int not in [0, 1]:
            self.log.info("无效的方向，请输入 1 或 0")
            return
        direction_byte = direction_int.to_bytes(1, byteorder='big')
        command = [self.address, 0x02, address, 0x00, direction_byte[0], 0x55]
        return self.send_command(command)

    def set_pump_speed(self, address: int, speed: int):
        """
        设置蠕动泵速度
        :param address: 蠕动泵设备地址
        :param speed: 速度值 (0-65535)
        """
        speed = int(speed)
        if speed < 0 or speed > 65535:
            self.log.info("速度值超出范围，请输入 0-65535")
            return
        high_byte = (speed >> 8) & 0xFF
        low_byte = speed & 0xFF
        command = [self.address, 0x03, address, high_byte, low_byte, 0x55]
        return self.send_command(command)

    def valve_control(self, state: int):
        """
        控制三通阀门开关
        :param state: 1=打开, 0=关闭
        1 = 蠕动泵端关
        0 = 气泵端关
        """
        state_int = int(state)
        if state_int not in [0, 1]:
            self.log.info("无效的阀门状态，请输入 1 或 0")
            return
        state_byte = state_int.to_bytes(1, byteorder='big')
        command = [self.address, 0x05, state_byte[0], 0x55, 0x55, 0x55]
        return self.send_command(command)

    def air_pump_control(self, state: int):
        """
        控制气泵开关
        :param state: 1=打开, 0=关闭
        """
        state_int = int(state)
        if state_int not in [0, 1]:
            self.log.info("无效的阀门状态，请输入 1 或 0")
            return
        state_byte = state_int.to_bytes(1, byteorder='big')
        command = [self.address, 0x06, state_byte[0], 0x55, 0x55, 0x55]
        return self.send_command(command)

    def pump_query(self, address: int):
        """
        查询蠕动泵开关、方向、速度
        :param address: 蠕动泵设备地址
        """
        command = [self.address, 0x09, address, 0x00, 0x00, 0x55]
        return self.send_command(command)
