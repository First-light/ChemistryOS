import struct
from serial.tools import list_ports
import serial
import os
import time

def extract_and_convert_temperature(hex_data):
    # 确保传入的数据是bytes类型
    if not isinstance(hex_data, bytes) or len(hex_data) != 7:
        raise ValueError("Invalid bytes data provided")

    # 使用struct解包为有符号整数
    result = int.from_bytes(hex_data[3:5], byteorder='big', signed=False)

    return result/10

def crc16_modbus(data):
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

def serial_examine(user_com):
    buffer = [0x11, 0x03, 0x00, 0x00, 0x00, 0x01]
    crc_bytes = crc16_modbus(buffer)
    buffer.extend(crc_bytes)
    # command = bytearray([0x00, 0x03, 0x00, 0x00, 0x00, 0x01, 0x85, 0xDB])
    command = bytearray(buffer)
    while(1):
        try:
            with serial.Serial(user_com, 9600) as ser:
                ser.write(command)
                time.sleep(0.05)
                response = ser.read(ser.in_waiting)
                print("Received response:", response.hex())
                result = extract_and_convert_temperature(response)
                print("Received response:", result," 度")
        except Exception as e:
            print("Error:", str(e))
            # break
        time.sleep(0.25)

def main():
    user_com = '/dev/ttyUSB_485'

    serial_examine(user_com)

if __name__ == "__main__":
    main()