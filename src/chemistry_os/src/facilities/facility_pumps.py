import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from structs import FacilityState
from time import sleep
from serial.tools import list_ports
import serial
import time

class PumpGroup(Facility):
    type = "pumps"

    def __init__(self,name:str):
        super().__init__(name,PumpGroup.type)


    def cmd_init(self):
        self.parser.register("wait", self.wait, {"time": 0}, "wait for time")

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
    
    def wait(self,time):
        print("wait ",time)
        sleep(time)

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
    
    def writespeed(self,usb_name, addr, speed):
        speed=int(speed)
        if speed>1500:
            print("转速过高！")
            return
        elif speed<0: 
            print("转速过低！")
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
        try:
            with serial.Serial(port=usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def startadd(self,usb_name, addr):
        buffer = []
        buffer.append(addr)
        buffer = buffer + [0x06, 0x00, 0x00, 0x00, 0x01]
        crc_result = self.crc16_modbus(buffer)
        swapped = (crc_result >> 8) | ((crc_result & 0xFF) << 8)
        buffer.append(swapped >> 8)
        buffer.append(swapped & 0xFF)
        command = bytearray(buffer)
        try:
            with serial.Serial(port=usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def stopadd(self,usb_name, addr):
        buffer = []
        buffer.append(addr)
        buffer = buffer + [0x06, 0x00, 0x00, 0x00, 0x00]
        crc_result = self.crc16_modbus(buffer)
        swapped = (crc_result >> 8) | ((crc_result & 0xFF) << 8)
        buffer.append(swapped >> 8)
        buffer.append(swapped & 0xFF)
        command = bytearray(buffer)
        try:
            with serial.Serial(port=usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))
    def liquid_wash(self,name, addr, rpm, tim):
        if name=='ice':
            usb_name = '/dev/ttyUSBice_wash'
        if name=='HCl':
            usb_name = '/dev/ttyUSBHCl_wash'
        self.writespeed(usb_name, addr, rpm*10)
        self.startadd(usb_name, addr)
        time.sleep(tim)
        self.stopadd(usb_name, addr)
    # 新版函数通过体积和转速计算需求的时间（根据9.13测试的数据），接受以下参数：
    # rpm转速round per minute,volume体积(ml)
    def add_liquid(self,name, addr, rpm, volume):
        
        if name=='H2O2':
            usb_name = '/dev/ttyUSBKH'
            addr=0x02
        if name=='KMnO4':
            addr=0x01
            usb_name = '/dev/ttyUSBKH'
        if name=='addHCl':
            usb_name = '/dev/ttyUSBaddHCl'
        speed = 0.0525 * rpm# 滴加速率：ml/min，测试日期9.13
        tim = volume / speed * 60 # 滴加时间
        print(f"滴加液体为{name},体积为{volume}ml,转速为{rpm}rpm，预期需要{tim}s")
        
        self.writespeed(usb_name, addr, rpm*10)
        time.sleep(1)
        self.startadd(usb_name, addr)
        interactable_countdown(tim)
        # time.sleep(tim)
        self.stopadd(usb_name, addr)

