import time
from time import sleep
from serial.tools import list_ports
import serial
from structs import FacilityState
from facility import Facility
import sys
sys.path.append('src/chemistry_os/src')


class Bath(Facility):
    type = "bath"

    def __init__(self, name: str, com: str):
        super().__init__(name, Bath.type)

    def cmd_init(self):
        self.parser.register("wait", self.wait, {"time": 0}, "wait for time")
        self.parser.register("cold", self.cold_ctr, {"on": 0}, "cold control")
        self.parser.register("hot", self.hot_ctr, {"on": 0}, "hot control")
        self.parser.register("mix", self.mix_ctr, {"on": 0}, "mix control")
        self.parser.register("circle", self.circle_ctr, {
                             "on": 0}, "circle control")
        self.parser.register("tmp", self.writetmp, {
                             "num": 0}, "set temperature")
        self.parser.register("readtmp", self.readtmp, {
                             "test": 0}, "read temperature")
        self.parser.register("readsettmp", self.readsettmp,
                             {}, "read set temperature")
        self.parser.register(
            "readworking", self.read_working, {}, "read working status")

    def cmd_error(self):
        print("error")

    def cmd_stop(self):
        print("stop")

    def listen(self):
        while True:
            if self.state == FacilityState.ERROR:
                break
            if self.state == FacilityState.STOP:
                break
            sleep(0.005)

    def wait(self, time):
        print("wait ", time)
        sleep(time)

    def check_status():
        """
        此为水浴锅状态查询函数
        接受字符串作为查询的动作类型
        返回查询结果
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            print("水浴端口未找到！")
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x07, 0x00, 0x01, 0x35, 0xCB])
        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                res = int.from_bytes(response[3:5], byteorder='big')
                print(response)
                return res

        except Exception as e:
            print("Error1:", str(e))

    def cold_ctr(on):
        """
        此为加热状态控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            print(port.device)
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            print("水浴端口未找到！")
            return ERROR

        # 查询搅拌器状态
        statu = Bath.check_status()
        statu_cold = (statu >> 4) & 1

        time.sleep(0.1)  # 查询后提供一点延时，否则会干扰后续写操作

        # 仅有当搅拌器状态与要求的状态不同时才进行状态转换
        if statu_cold == 1 and on == 0:
            print("制冷允许关闭")
        elif statu_cold == 0 and on == 1:
            print("制冷允许开启")
        else:
            print("制冷状态不变")
            return
        command = bytearray([0x01, 0x06, 0x00, 0x07, 0x00, 0x10, 0x39, 0xC7])
        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def hot_ctr(on):
        """
        此为加热状态控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            print(port.device)
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            print("水浴端口未找到！")
            return ERROR

        # 查询搅拌器状态
        statu = Bath.check_status()
        statu_hot = (statu >> 3) & 1

        time.sleep(0.1)  # 查询后提供一点延时，否则会干扰后续写操作

        # 仅有当搅拌器状态与要求的状态不同时才进行状态转换
        if statu_hot == 1 and on == 0:
            print("加热允许关闭")
        elif statu_hot == 0 and on == 1:
            print("加热允许开启")
        else:
            print("加热状态不变")
            return
        command = bytearray([0x01, 0x06, 0x00, 0x07, 0x00, 0x08, 0x39, 0xCD])
        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def mix_ctr(on):
        """
        此为搅拌器控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            return ERROR

        # 查询搅拌器状态
        statu = Bath.check_status()
        statu_mix = (statu >> 6) & 1

        time.sleep(0.1)  # 查询后提供一点延时，否则会干扰后续写操作

        # 仅有当搅拌器状态与要求的状态不同时才进行状态转换
        if statu_mix == 1 and on == 0:
            print("搅拌器关闭")
        elif statu_mix == 0 and on == 1:
            print("搅拌器开启")
        else:
            print("搅拌器状态不变")
            return
        command = bytearray([0x01, 0x06, 0x00, 0x07, 0x00, 0x40, 0x39, 0xFB])

        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def circle_ctr(on):
        """
        此为循环系统控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            return ERROR

        # 查询搅拌器状态
        statu = Bath.check_status()
        statu_cir = (statu >> 5) & 1

        time.sleep(0.1)  # 查询后提供一点延时，否则会干扰后续写操作

        # 仅有当搅拌器状态与要求的状态不同时才进行状态转换
        if statu_cir == 1 and on == 0:
            print("循环系统关闭")
        elif statu_cir == 0 and on == 1:
            print("循环系统开启")
        else:
            print("循环系统状态不变")
            return
        command = bytearray([0x01, 0x06, 0x00, 0x07, 0x00, 0x20, 0x39, 0xD3])

        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def convert_and_split_hex(value):
        if value < 0:
            value = (1 << 16) + value
        hex_str = f"{value:04X}"
        high_part = int(hex_str[:2], 16)
        low_part = int(hex_str[2:], 16)

        return high_part, low_part

    def crc16_modbus(data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                lsb = crc & 1
                crc >>= 1
                if lsb:
                    crc ^= 0xA001
        return crc

    def writetmp(num):
        ERROR = -1
        OVERRANGE = -2
        num *= 10
        if num > 3000:
            print("温度过高！")
            return OVERRANGE
        elif num < -900:
            print("温度过低！")
            return OVERRANGE

        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            print(port.device)
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            print("水浴端口未找到！")
            return ERROR

        a, b = Bath.convert_and_split_hex(num)
        buffer = [0x01, 0x06, 0x00, 0x02]
        buffer.append(a)
        buffer.append(b)
        crc_result = Bath.crc16_modbus(buffer)

        swapped = (crc_result >> 8) | ((crc_result & 0xFF) << 8)

        buffer.append(swapped >> 8)
        buffer.append(swapped & 0xFF)

        command = bytearray(buffer)
        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def read_working():
        """
        读取是否正在加热或制冷
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x08, 0x00, 0x01, 0x05, 0xC8])
        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                res = int.from_bytes(response[3:5], byteorder='big')
                hot_working = res & 1
                cold_working = (res >> 3) & 1
                print(response)
                print("是否正在加热：", hot_working)
                print("是否正在制冷：", cold_working)

        except Exception as e:
            print("Error1:", str(e))

    def readsettmp():
        """
        读取设置的工作温度
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x02, 0x00, 0x01, 0x25, 0xCA])
        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                res = int.from_bytes(response[3:5], byteorder='big')
                print(res/10)

        except Exception as e:
            print("Error1:", str(e))

    def readtmp(test=0):
        """
        读取当前温度
        """
        ERROR = -1
        pd = False
        plist = list(list_ports.comports())
        for port in plist:
            if Bath.bath_com in port.device:
                pd = True
                break
        if pd == False:
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A])
        try:
            with serial.Serial(Bath.bath_com, 9600, timeout=1) as ser:
                if test:
                    print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                while response == b'':
                    print("!!!")
                    ser.write(command)
                    time.sleep(0.2)
                    response = ser.read(ser.in_waiting)
                res = int.from_bytes(
                    response[3:5], byteorder='big', signed=False)
                # 检查最高位是否为1（负数）
                if res & 0x8000:
                    # 如果是负数，进行二进制补码转换
                    res = res - 0x10000
                res /= 10.0
                if test:
                    print(' ')
                    print(response[3:5])
                    print(response)
                    print(res)
                return res

        except Exception as e:
            print("Error1:", str(e))
