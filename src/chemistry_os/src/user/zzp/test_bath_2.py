import struct
from serial.tools import list_ports
import serial
import os
import time

def extract_and_convert_temperature(hex_data):
    # 确保传入的数据是bytes类型
    # 增加长度判断，防止解析空包报错
    if not isinstance(hex_data, bytes) or len(hex_data) < 5: 
        return None # 数据过短不解析

    # 使用struct解包为有符号整数 (这里假设取第3、4位数据)
    try:
        result = int.from_bytes(hex_data[3:5], byteorder='big', signed=False)
        return result/10
    except:
        return 0

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
    # --- 1. 准备命令 (发往地址 0x11) ---
    buffer = [0x11, 0x03, 0x00, 0x00, 0x00, 0x01]
    crc_bytes = crc16_modbus(buffer)
    buffer.extend(crc_bytes)
    command = bytearray(buffer)

    print(f"当前发送命令: {command.hex()}")
    print("正在监听是否有地址 00 的异常回复...")

    try:
        # --- 2. 串口操作移到循环外，保持连接稳定，防止漏掉偶发数据 ---
        # timeout设置读取超时，避免没有数据时无限卡死
        with serial.Serial(user_com, 9600, timeout=0.5) as ser:
            while True:
                try:
                    # 清空输入缓存，确保读到的是本次回复
                    ser.reset_input_buffer()

                    # 发送命令
                    ser.write(command)

                    # 等待回复 (根据设备响应速度调整)
                    time.sleep(0.1)

                    # 读取缓冲区所有数据
                    if ser.in_waiting:
                        response = ser.read(ser.in_waiting)
                    else:
                        response = b'' # 无数据

                    # 打印当前交互 (方便调试观察)
                    if response:
                        print(f"Recv: {response.hex()}")

                        # --- 3. 核心修改：检测是否存在地址为 00 的回复 ---
                        if len(response) > 0 and response[0] == 0x00:
                            print("\n" + "="*40)
                            print("!!! 捕捉到地址 00 的回复 !!!")
                            print(f"异常回复内容: {response.hex()}")

                            # 保存触发该回复的【命令】到文件
                            filename = "trigger_command_00.txt"
                            with open(filename, "w") as f:
                                f.write(command.hex())

                            print(f"已将触发命令保存至: {filename}")
                            print("="*40 + "\n")


                        # 正常解析温度 (只有当回复地址匹配 0x11 且长度足够时)
                        elif len(response) >= 7 and response[0] == 0x11:
                            result = extract_and_convert_temperature(response)
                            if result is not None:
                                print("解析温度:", result, "度")

                except Exception as e_inner:
                    print("Communication Error:", str(e_inner))

                # 循环间隔
                # time.sleep(0.25)

    except Exception as e:
        print("Serial Port Error:", str(e))

def main():
    # 请确认此处端口号
    user_com = '/dev/ttyUSB_485'

    serial_examine(user_com)

if __name__ == "__main__":
    main()