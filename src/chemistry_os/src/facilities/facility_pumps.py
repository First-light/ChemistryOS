import sys
sys.path.append('src/chemistry_os/src')
import serial
import time
from facility import Facility
from utilities.events import event_countdown
from facilities.flowdisplay import Flowdisplay
from utilities.utility_param import ParamUtils

class PumpGroup(Facility):

    usb_name='/dev/ttyUSB0'
    type='add_Liquid'
    reverse=True
    base_speed=0.0675 # ml/min

    def __init__(self, name: str):
        super().__init__(name, PumpGroup.type)
        self.init_dict = ParamUtils.get_init_params(self)
        self.data_dict = {
            "HCl":{
                'addr': 0x12,
                'direction': 1,
                'speed': 0,
                'on_off': 0
            },
            "KMnO4":{
                'addr': 0x13,
                'direction': 1,
                'speed': 0,
                'on_off': 0
            },
            "H2O2":{
                'addr': 0x14,
                'direction': 1,
                'speed': 0,
                'on_off': 0
            },
            "N2H4":{
                'addr': 0x15,
                'direction': 1,
                'speed': 0,
                'on_off': 0
            }
        }
        self.add_liquid_config = {
            "HCl":{
                'addr': 0x12,
                'pipe_volume': 3.14 * 0.08 * 0.08 * 180
            },
            "HCl_wash":{
                'addr': 0x12,
                'pipe_volume': 3.14 * 0.08 * 0.08 * 180
            },
            "KMnO4":{
                'addr': 0x13,
                'pipe_volume': 3.14 * 0.08 * 0.08 * 180
            },
            "H2O2":{
                'addr': 0x14,
                'pipe_volume': 3.14 * 0.08 * 0.08 * 180
            },
            "N2H4":{
                'addr': 0x15,
                'pipe_volume': 3.14 * 0.08 * 0.08 * 180
            }
        }

    def update_data_dict(self, addr, direction=None, speed=None, on_off=None):
        """
        更新数据字典，支持通过名称或地址进行更新
        :param identifier: 可以是名称(str)或地址(int)
        """
        name = None
        
        # 判断标识符类型并找到对应的名称
        if isinstance(addr, str):
            # 通过名称查找
            if addr in self.data_dict:
                name = addr
        elif isinstance(addr, int):
            # 通过地址查找名称
            for pump_name, data in self.data_dict.items():
                if data['addr'] == addr:
                    name = pump_name
                    break
        
        # 更新数据
        if name:
            if direction is not None:
                self.data_dict[name]['direction'] = direction
            if speed is not None:
                self.data_dict[name]['speed'] = speed
            if on_off is not None:
                self.data_dict[name]['on_off'] = on_off
        else:
            self.log.warning(f"未找到标识符为 {addr} 的泵")

    def cmd_init(self):
        """
        注册指令
        """
        self.parser.register("init", self.cmd_init, {}, "初始化泵组")
        self.parser.register("writespeed", self.writespeed, {
            "addr": 0, "speed": 0.0}, "设置泵的转速")
        self.parser.register("startadd", self.startadd, {
            "addr": 0}, "启动泵")
        self.parser.register("stopadd", self.stopadd, {
            "addr": 0}, "停止泵")
        self.parser.register("liquid_wash", self.liquid_wash, {
            "name": "", "rpm": 0.0, "tim": 0.0}, "清洗液体")
        self.parser.register("add_liquid", self.add_liquid, {
            "name": "", "rpm": 0.0, "volume": 0.0}, "添加液体")

    def cmd_error_handing(self):
        self.stopadd(0x12)
        self.stopadd(0x13)
        self.stopadd(0x14)
        self.stopadd(0x15)
        pass

    def cmd_stop_handing(self):
        self.stopadd(0x12)
        self.stopadd(0x13)
        self.stopadd(0x14)
        self.stopadd(0x15)
        pass

    def cmd_reset(self):#从error/stop恢复idle的状态
        pass

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
        # 返回低字节在前，高字节在后的字节列表（Modbus协议要求）
        return [crc & 0xFF, (crc >> 8) & 0xFF]
    
    def writedirection(self, addr, forward=1):
        buffer = [addr, 0x06, 0x00, 0x01, 0x00, forward]
        crc_bytes = self.crc16_modbus(buffer)
        buffer.extend(crc_bytes)
        command = bytearray(buffer)
        self.log.info(f"生成的命令: {command}")
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command)
                time.sleep(0.05)
                response = ser.read(ser.in_waiting)
                self.log.info(f"设备响应: {response}")
            self.update_data_dict(addr=addr, direction=forward)

        except Exception as e:
            self.log.info(f"发送命令失败: {str(e)}")
    
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
        crc_bytes = self.crc16_modbus(buffer)
        buffer.extend(crc_bytes)

        command = bytearray(buffer)
        self.log.info(f"生成的命令: {command}")
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command)
                time.sleep(0.05)
                response = ser.read(ser.in_waiting)
                self.log.info(f"设备响应: {response}")
            self.update_data_dict(addr=addr, speed=speed)

        except Exception as e:
            self.log.info(f"发送命令失败: {str(e)}")

    def startadd(self, addr):
        buffer = []
        buffer.append(addr)
        buffer = buffer + [0x06, 0x00, 0x00, 0x00, 0x01]
        crc_bytes = self.crc16_modbus(buffer)
        buffer.extend(crc_bytes)
        command = bytearray(buffer)
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command)
                time.sleep(0.05)
                response = ser.read(ser.in_waiting)
                self.log.info(f"设备响应: {response}")
            self.update_data_dict(addr=addr, on_off='on')

        except Exception as e:
            self.log.info("Error1:", str(e))

    def stopadd(self, addr):
        buffer = []
        buffer.append(addr)
        buffer = buffer + [0x06, 0x00, 0x00, 0x00, 0x00]
        crc_bytes = self.crc16_modbus(buffer)
        buffer.extend(crc_bytes)
        command = bytearray(buffer)
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                self.log.info("成功连接")
                ser.write(command)
                time.sleep(0.05)
                response = ser.read(ser.in_waiting)
                self.log.info(f"设备响应: {response}")
            self.update_data_dict(addr=addr, on_off='off')

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
        pipe_volume = self.add_liquid_config[name]['pipe_volume']
        speed = self.base_speed * rpm
        tim = (volume + pipe_volume) / speed * 60 # 滴加时间
        Info = {
            '进料液体': name,
            '进料转速': str(rpm) + ' 转/min',
            '进料速度': str(speed) + ' ml/min',
            '目标体积': str(volume) + ' ml',
            '预期时间': str(tim) + ' s'
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='液料滴加', Info=Info)

        addr = self.add_liquid_config[name]['addr']

        self.log.info(f"滴加液体为{name},体积为{volume}ml,转速为{rpm}rpm，预期需要{tim}s")

        self.writespeed(addr, rpm*10)
        time.sleep(1)
        self.startadd(addr)
        event_countdown(tim, name=name, volume=volume, rpm=rpm)
        self.stopadd(addr)
        if self.reverse == True:
            self.liquid_back(name)

    def liquid_back(self, name, rpm=150):
        addr = self.add_liquid_config[name]['addr']
        pipe_volume = self.add_liquid_config[name]['pipe_volume']
        speed = self.base_speed * rpm
        pipe_time = pipe_volume / speed * 60
        self.writespeed(addr, rpm*10)
        self.writedirection(0)
        self.startadd(addr)
        event_countdown(pipe_time, name=name, volume=pipe_volume, rpm=rpm, directon=0)
        self.stopadd(addr)
        self.writedirection(1)


if __name__ == "__main__":
    add_Liquid=PumpGroup('add_Liquid')

    # add_Liquid.writespeed(0x12, 100)
    # add_Liquid.writespeed(0x13, 100)
    # add_Liquid.writespeed(0x14, 100)
    # add_Liquid.writespeed(0x15, 100)

    add_Liquid.add_liquid('HCl', 150, 180)