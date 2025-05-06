# coding=utf-8

import struct
from serial.tools import list_ports
import serial
import time

# 此处为称量模块端口


class Add_solid:
    solid_com = '/dev/ttyUSB1'

    def extract_and_convert(hex_data):
        # 确保传入的数据是bytes类型                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
        if not isinstance(hex_data, bytes) or len(hex_data) != 9:
            raise ValueError("Invalid bytes data provided")

        bytes_data = hex_data[3:7]
        
        # 使用struct解包为有符号整数
        result = struct.unpack('>i', bytes_data)[0]

        return result
    def opentest():
        OK=0
        ERROR=-1
        user_com1 = Add_solid.solid_com
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x02, 0xc4, 0x0b])
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                ser.write(command)
                response = ser.read(9)
                print(f'response: {response}')
                for i, byte in enumerate(response):
                    print(f"0x{byte:02x}",end=' ')
                print(' ')
        except Exception as e:
            print("Error1:", str(e))
        time.sleep(4)

    def openjaw():
        OK=0
        ERROR=-1
        user_com1 = Add_solid.solid_com
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x42, 0x00, 0x00, 0x00, 0x00])
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                while True:
                    if ser.in_waiting >= 34:
                        # 读取 26 字节的数据
                        response = ser.read(34)
                        ser.write(command)
                        print(f'response: {response}')
                        for i, byte in enumerate(response):
                            print(f"0x{byte:02x}",end=' ')
                        print(' ')
                        break
        except Exception as e:
            print("Error1:", str(e))
        time.sleep(4)
    
    def closejaw():
        OK=0
        ERROR=-1
        user_com1 = Add_solid.solid_com
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x43, 0x00, 0x00, 0x00, 0x00])
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                while True:
                    if ser.in_waiting >= 34:
                        # 读取 26 字节的数据
                        response = ser.read(34)
                        ser.write(command)
                        print(f'response: {response}')
                        for i, byte in enumerate(response):
                            print(f"0x{byte:02x}",end=' ')
                        print(' ')
                        break
        except Exception as e:
            print("Error1:", str(e))
        time.sleep(4)

    def spin_on():
        OK=0
        ERROR=-1
        user_com1 = Add_solid.solid_com
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x44, 0x00, 0x00, 0x00, 0x00])
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                while True:
                    if ser.in_waiting >= 34:
                        # 读取 26 字节的数据
                        response = ser.read(34)
                        ser.write(command)
                        print(f'response: {response}')
                        for i, byte in enumerate(response):
                            print(f"0x{byte:02x}",end=' ')
                        print(' ')
                        break
        except Exception as e:
            print("Error1:", str(e))
        time.sleep(8)

    def spin_off():
        OK=0
        ERROR=-1
        user_com1 = Add_solid.solid_com
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x45, 0x00, 0x00, 0x00, 0x00])
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                while True:
                    if ser.in_waiting >= 34:
                        # 读取 26 字节的数据
                        response = ser.read(34)
                        ser.write(command)
                        print(f'response: {response}')
                        for i, byte in enumerate(response):
                            print(f"0x{byte:02x}",end=' ')
                        print(' ')
                        break
        except Exception as e:
            print("Error1:", str(e))
        time.sleep(8)

    def set_k(kp, kd, offset):
        OK=0
        ERROR=-1
        OVERRANGE=-2
        packed_kp = struct.pack('f', kp)
        packed_kd = struct.pack('f', kd)
        packed_offset = struct.pack('f', offset)
        user_com1 = Add_solid.solid_com
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        byte_array_data = bytearray([0x01, 0x46])
        command = byte_array_data + packed_kp + packed_kd + packed_offset
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                while True:
                    if ser.in_waiting >= 34:
                        # 读取 26 字节的数据
                        response = ser.read(34)
                        ser.write(command)
                        print(f'response: {response}')
                        for i, byte in enumerate(response):
                            print(f"0x{byte:02x}",end=' ')
                        print(' ')
                        break
                
        except Exception as e:
            print("Error1:", str(e))

    def add_solid(set_point):
        OK=0
        ERROR=-1
        OVERRANGE=-2
        packed_data = struct.pack('f', set_point)
        user_com1 = Add_solid.solid_com
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        byte_array_data = bytearray([0x01, 0x47])
        command = byte_array_data + packed_data
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                while True:
                    if ser.in_waiting >= 34:
                        # 读取 26 字节的数据
                        response = ser.read(34)
                        ser.write(command)
                        print(f'response: {response}')
                        for i, byte in enumerate(response):
                            print(f"0x{byte:02x}",end=' ')
                        print(' ')
                        break
                
        except Exception as e:
            print("Error1:", str(e))
    
    def read():
        OK=0
        ERROR=-1
        OVERRANGE=-2
        user_com1 = Add_solid.solid_com
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if user_com1 in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        # exit()
        try:
            with serial.Serial(user_com1, 9600, timeout=0.15) as ser:
                print("成功连接ACM")
                
                while True:
                    if ser.in_waiting >= 34:
                        # 读取 26 字节的数据
                        response = ser.read(34)
                        print(f'response: {response}')
                        for i, byte in enumerate(response):
                            print(f"0x{byte:02x}",end=' ')
                        print(' ')
                
        except Exception as e:
            print("Error1:", str(e))

if __name__ == "__main__":
    # Add_solid.add_solid(0.5 * 100)
    Add_solid.opentest()
    exit()
    Add_solid.openjaw()
    Add_solid.closejaw()
    # Add_solid.spin_on()
    # Add_solid.spin_off()
    # Add_solid.add_solid(1.0)
    # Add_solid.read()