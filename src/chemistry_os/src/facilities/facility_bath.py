import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from structs import FacilityState
from time import sleep
from serial.tools import list_ports
import serial
import time
import threading
import sys
import select

class Bath(Facility):
    type = "bath"
    public_param_1 = 0
    public_param_2 = 1
    bath_com = '/dev/ttyUSB0'

    def __init__(self,name:str):
        super().__init__(name,self.type)
        

    def output(self,param1,param2):
        print("output:",param1,param2)

    def cmd_init(self):
        self.parser.register("output", self.output, {"param1": 0, "param2": 1}, "output test")
        self.parser.register("message", self.message,{}, "output message")
        self.parser.register("wait", self.wait, {"time": 0}, "wait for time")
        self.parser.register("control", self.control, {}, "control")

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


    def message(self):
        print("This is a temp facility")
        print("name:",self.name)
    
    def wait(self,time):
        print("wait ",time)
        sleep(time)

    def control(self):
        print("control")
        user_input = input("Please enter any character: ")
        print("You entered:", user_input)

    def check_status(self):
        """
        此为水浴锅状态查询函数
        接受字符串作为查询的动作类型
        返回查询结果
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            print("水浴端口未找到！")
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x07, 0x00, 0x01, 0x35, 0xCB])
        try:
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                res = int.from_bytes(response[3:5], byteorder='big')
                print(response)
                return res
                
        except Exception as e:
            print("Error1:", str(e))
        
    def cold_ctr(self, on):
        """
        此为加热状态控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            print("水浴端口未找到！")
            return ERROR
        
        # 查询搅拌器状态
        statu = self.check_status()
        statu_cold = (statu >> 4) & 1
        
        time.sleep(0.1)# 查询后提供一点延时，否则会干扰后续写操作

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
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def hot_ctr(self, on):
        """
        此为加热状态控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            print("水浴端口未找到！")
            return ERROR
        
        # 查询搅拌器状态
        statu = self.check_status()
        statu_hot = (statu >> 3) & 1
        
        time.sleep(0.1)# 查询后提供一点延时，否则会干扰后续写操作

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
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def mix_ctr(self, on):
        """
        此为搅拌器控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        
        # 查询搅拌器状态
        statu = self.check_status()
        statu_mix = (statu >> 6) & 1
        
        time.sleep(0.1)# 查询后提供一点延时，否则会干扰后续写操作

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
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def circle_ctr(self, on):
        """
        此为循环系统控制函数
        接受整数作为控制搅拌器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        
        # 查询搅拌器状态
        statu = self.check_status()
        statu_cir = (statu >> 5) & 1
        
        time.sleep(0.1)# 查询后提供一点延时，否则会干扰后续写操作

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
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

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

    def writetmp(self, num):
        ERROR=-1
        OVERRANGE=-2
        num*=10
        if num>3000: 
            print("温度过高！")
            return OVERRANGE
        elif num<-900: 
            print("温度过低！")
            return OVERRANGE
        
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            print (port.device)
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            print("水浴端口未找到！")
            return ERROR
        
        a, b = self.convert_and_split_hex(num)
        buffer = [0x01, 0x06, 0x00, 0x02]
        buffer.append(a)
        buffer.append(b)
        crc_result = self.crc16_modbus(buffer)

        swapped = (crc_result >> 8) | ((crc_result & 0xFF) << 8)

        buffer.append(swapped >> 8)
        buffer.append(swapped & 0xFF)
        
        command = bytearray(buffer)
        try:
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                print(response)

        except Exception as e:
            print("Error1:", str(e))

    def read_working(self):
        """
        读取是否正在加热或制冷
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x08, 0x00, 0x01, 0x05, 0xC8])
        try:
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
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

    def readsettmp(self):
        """
        读取设置的工作温度
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x02, 0x00, 0x01, 0x25, 0xCA])
        try:
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                print("成功连接")
                ser.write(command)
                time.sleep(0.1)
                response = ser.read(ser.in_waiting)
                res = int.from_bytes(response[3:5], byteorder='big')
                print(res/10)

        except Exception as e:
            print("Error1:", str(e))

    def readtmp(self, test=0):
        """
        读取当前温度
        """
        ERROR=-1
        pd=False
        plist = list(list_ports.comports())
        for port in plist:
            if self.bath_com in port.device:
                pd=True
                break
        if pd==False:
            return ERROR
        command = bytearray([0x01, 0x03, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A])
        try:
            with serial.Serial(self.bath_com, 9600, timeout=1) as ser:
                if test:
                    print("成功连接")
                ser.write(command)
                time.sleep(0.2)
                response = ser.read(ser.in_waiting)
                while response==b'':
                    print("!!!")
                    ser.write(command)
                    time.sleep(0.2)
                    response = ser.read(ser.in_waiting)
                res = int.from_bytes(response[3:5], byteorder='big', signed=False)
                # 检查最高位是否为1（负数）
                if res & 0x8000:
                    # 如果是负数，进行二进制补码转换
                    res = res - 0x10000
                res/=10.0
                if test:
                    print(' ')
                    print(response[3:5])
                    print(response)
                    print(res)
                return res

        except Exception as e:
            print("Error1:", str(e))

    def interactable_writetmp(self, tmp):
        # 用于控制是否继续计时的事件
        stop_event = threading.Event()
        countdown_finished_event = threading.Event()
        def wait_tmp(tmp):
            now_tmp = self.readtmp()# 避免短时间内多次调用温度读取函数，以免读到错误数值
            start_tmp = now_tmp+0.001
            start_time = time.time()
            self.writetmp(tmp)# 设置水浴锅温度
            print('控温中...')
            while(now_tmp > tmp+5 or now_tmp < tmp-5) and not stop_event.is_set():
                bias = 5 if abs(tmp + 5 - start_tmp) < abs(tmp - 5 - start_tmp) else -5
                remaining_time = (tmp - now_tmp + bias)/((now_tmp - start_tmp)/(time.time() - start_time))
                if remaining_time<0:
                    remaining_time*=-1
                # 计算预计完成时间
                finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+remaining_time))
                print(f"当前温度为：{now_tmp},未达到指定温度{tmp}附近，继续控温，预计剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}, 输入 \'q\' 以跳过", end="\r")
                time.sleep(1)
                now_tmp = self.readtmp()
                continue
            if not stop_event.is_set():
                print(f"\n到达指定温度附近，当前温度为{now_tmp}，共耗时{time.time() - start_time}秒")
                countdown_finished_event.set()

        def check_exit():
            # 监听键盘输入，按 'q' 停止温控
            while not countdown_finished_event.is_set():
                if sys.stdin in select.select([sys.stdin], [], [], 1)[0]:  # 使用 select 监听输入
                    input_char = sys.stdin.read(1).strip()  # 读取输入字符
                    if input_char.lower() == 'q':
                        print("\n手动停止计时")
                        stop_event.set()  # 触发事件停止
                        break  # 停止监听输入，后续程序继续执行
            # print("计时结束，手动停止线程已退出")

        # 创建线程监听键盘输入
        exit_thread = threading.Thread(target=check_exit)
        exit_thread.daemon = True  # 设置为守护线程，使主线程结束时它自动退出
        exit_thread.start()

        # 启动温度控制
        wait_tmp(tmp)
