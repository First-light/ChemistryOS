import sys
sys.path.append('src/chemistry_os/src')
import threading
import serial
import time
import select
from facility import Facility

def interactable_countdown(seconds):
    # 用于控制是否继续计时的事件
    stop_event = threading.Event()
    countdown_finished_event = threading.Event()

    def countdown(seconds):
        start_time = time.time()  # 获取当前时间
        end_time = start_time + seconds  # 计算结束时间

        while seconds > 0 and not stop_event.is_set():  # 计时中如果stop_event触发就停止
            # 计算剩余时间
            now = time.time()
            remaining_time = end_time - now
            # 计算预计完成时间
            finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
            # 打印剩余时间和预计完成时间
            print(f"剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}, 输入 \'q\' 以跳过", end="\r")
            time.sleep(1)
            seconds -= 1

        if not stop_event.is_set():
            print("\n时间到")
            countdown_finished_event.set()

    def check_exit():
        # 监听键盘输入，按 'q' 停止倒计时
        while not countdown_finished_event.is_set():
            if sys.stdin in select.select([sys.stdin], [], [], 1)[0]:  # 使用 select 监听输入
                input_char = sys.stdin.read(1).strip()  # 读取输入字符
                if input_char.lower() == 'q':
                    print("\n手动停止计时")
                    stop_event.set()  # 触发事件停止倒计时
                    break  # 停止监听输入，后续程序继续执行
        # print("计时结束，手动停止线程已退出")

    # 创建线程监听键盘输入
    exit_thread = threading.Thread(target=check_exit)
    exit_thread.daemon = True  # 设置为守护线程，使主线程结束时它自动退出
    exit_thread.start()

    # 启动倒计时
    countdown(seconds)

class Add_Liquid(Facility):

    usb_name='/dev/ttyUSB0'
    type='add_Liquid'

    def __init__(self, name: str):
        super().__init__(name, Add_Liquid.type)

    def cmd_init(self):
        pass

    def cmd_error(self):
        print("error")

    def cmd_stop(self):
        print("stop")

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
        print(command)
        try:
            with serial.Serial(port=self.usb_name, baudrate=9600, timeout=1, stopbits=2) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

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
                print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

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
                print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))
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
            addr=0x03
        elif name=='KMnO4':
            addr=0x04
        elif name=='H2O2':
            addr=0x05
        elif name=='CH3CN':
            addr=0x06
        elif name=='N2H4':
            addr=0x07
        speed = 0.0675 * rpm# 滴加速率：ml/min，测试日期9.13 0.0525
        tim = volume / speed * 60 # 滴加时间
        print(f"滴加液体为{name},体积为{volume}ml,转速为{rpm}rpm，预期需要{tim}s")
        
        self.writespeed(addr, rpm*10)
        time.sleep(1)
        self.startadd(addr)
        interactable_countdown(tim)
        # time.sleep(tim)
        self.stopadd(addr)


if __name__ == "__main__":
    add_Liquid=Add_Liquid('add_Liquid')
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