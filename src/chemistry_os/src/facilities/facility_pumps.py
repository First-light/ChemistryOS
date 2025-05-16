import sys
sys.path.append('src/chemistry_os/src')
import serial
import time
from facility import Facility
from tools.events import event_countdown

class PumpGroup(Facility):

    usb_name='/dev/ttyUSB0'
    type='add_Liquid'

    def __init__(self, name: str):
        super().__init__(name, PumpGroup.type)

    def cmd_init(self):
        """
        注册指令
        """
        self.parser.register("init", self.cmd_init, {}, "初始化泵组")
        self.parser.register("error", self.cmd_error, {}, "处理错误")
        self.parser.register("stop", self.cmd_stop, {}, "停止泵组")
        self.parser.register("writespeed", self.writespeed, {
            "addr": 0, "speed": 0}, "设置泵的转速")
        self.parser.register("startadd", self.startadd, {
            "addr": 0}, "启动泵")
        self.parser.register("stopadd", self.stopadd, {
            "addr": 0}, "停止泵")
        self.parser.register("liquid_wash", self.liquid_wash, {
            "name": "", "rpm": 0, "tim": 0}, "清洗液体")
        self.parser.register("add_liquid", self.add_liquid, {
            "name": "", "rpm": 0, "volume": 0}, "添加液体")

    def cmd_error(self):
        self.log.info("发生错误")

    def cmd_stop(self):
        self.log.info("停止泵组")

    def convert_and_split_hex(self, value):
        if value < 0:
            value = (1 << 16) + value
        hex_str = f"{value:04X}"
        high_part = int(hex_str[:2], 16)
        low_part = int(hex_str[2:], 16)
        
        return high_part, low_part
    
    def crc16_modbus(self, data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                lsb = crc & 1
                crc >>= 1
                if lsb:
                    crc ^= 0xA001
        return crc
    
    def writespeed(self, addr, speed):
        speed = int(speed)
        if speed > 1500:
            self.log.info("转速过高！")
            return
        elif speed < 0:
            self.log.info("转速过低！")
            return

        a, b = self.convert_and_split_hex(speed)
        buffer = []
        buffer.append(addr)
        buffer = buffer + [0x06, 0x00, 0x02]
        buffer.append(a)
        buffer.append(b)
        crc_result = self.crc16_modbus(buffer)
        swapped = (crc_result >> 8) | ((crc_result & 0xFF) << 8)
        buffer.append(swapped >> 8)
        buffer.append(swapped & 0xFF)

        command = bytearray(buffer)
        self.log.info(f"生成的命令: {command}")
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                self.log.info(f"设备响应: {response}")

        except Exception as e:
            self.log.info(f"发送命令失败: {str(e)}")

    def startadd(self, addr):
        buffer = []
        buffer.append(addr)
        buffer = buffer + [0x06, 0x00, 0x00, 0x00, 0x01]
        crc_result = self.crc16_modbus(buffer)
        swapped = (crc_result >> 8) | ((crc_result & 0xFF) << 8)
        buffer.append(swapped >> 8)
        buffer.append(swapped & 0xFF)
        command = bytearray(buffer)
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                self.log.info(f"设备响应: {response}")

        except Exception as e:
            self.log.info("Error1:", str(e))

    def stopadd(self, addr):
        buffer = []
        buffer.append(addr)
        buffer = buffer + [0x06, 0x00, 0x00, 0x00, 0x00]
        crc_result = self.crc16_modbus(buffer)
        swapped = (crc_result >> 8) | ((crc_result & 0xFF) << 8)
        buffer.append(swapped >> 8)
        buffer.append(swapped & 0xFF)
        command = bytearray(buffer)
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                self.log.info(f"设备响应: {response}")

        except Exception as e:
            self.log.info("Error1: " + str(e))
    def liquid_wash(self, name, rpm, tim):
        if name=='ice':
            addr=0x02
        if name=='HCl':
            addr=0x01
        self.writespeed(addr, rpm*10)
        self.startadd(addr)
        time.sleep(tim)
        self.stopadd(addr)
    # 新版函数通过体积和转速计算需求的时间（根据9.13测试的数据），接受以下参数：
    # rpm转速round per minute,volume体积(ml)
    def add_liquid(self, name, rpm, volume):
        if name=='HCl':
            addr=0x02
        elif name=='KMnO4':
            addr=0x03
        elif name=='H2O2':
            addr=0x04
        elif name=='CH3CN':
            addr=0x05
        elif name=='N2H4':
            addr=0x06
        speed = 0.0675 * rpm# 滴加速率：ml/min，测试日期9.13 0.0525
        tim = volume / speed * 60 # 滴加时间
        self.log.info(f"滴加液体为{name},体积为{volume}ml,转速为{rpm}rpm，预期需要{tim}s")
        
        self.writespeed(addr, rpm*10)
        time.sleep(1)
        self.startadd(addr)
        event_countdown(tim)
        # time.sleep(tim)
        self.stopadd(addr)


if __name__ == "__main__":
    add_Liquid=PumpGroup('add_Liquid')
    add_Liquid.writespeed(0x03, 100)
    add_Liquid.writespeed(0x04, 100)
    add_Liquid.writespeed(0x05, 100)
    # Add_liquid_fixed.startadd(0x02)
    # Add_liquid_fixed.stopadd(0x02)
    # Add_liquid_fixed.add_liquid('H2O2', 0x01, 14.3, 10)
    # Add_liquid_fixed.add_liquid('H2O2', 0x01, 100, 10)
    # Add_liquid_fixed.liquid_wash('ice', 0x01, rpm=150, tim=5)
    # Add_liquid_fixed.add_liquid('addHCl', rpm=150, volume=5)
    # add_Liquid.add_liquid('addHCl', rpm=100, volume=20)
    # add_Liquid.liquid_wash('addHCl', rpm=100, tim=5)
    # add_Liquid.writespeed(0x01, 0)
    # Add_liquid_fixed.stopadd('H2O2',0x01)