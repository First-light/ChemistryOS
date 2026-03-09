import sys
sys.path.append('src/chemistry_os/src')
import serial
import time
import threading
from facility import Facility
from facilities.flowdisplay import Flowdisplay
from utilities.utility_param import ParamUtils
from utilities.utility_log import LogUtils
from facilities.facility_parser import CommandParser

class PumpGroup(Facility):

    usb_name='/dev/ttyUSB_485'
    type='add_Liquid'
    reverse=True
    base_speed = 0.0595 # ml/min
    pipe_volume_max = 3.14 * 0.04 * 0.04 * 280

    def __init__(self, name: str):
        super().__init__(name, PumpGroup.type)
        self.bath = None
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
            },
            "CH3CH":{
                'addr': 0x16,
                'direction': 1,
                'speed': 0,
                'on_off': 0
            }
        }
        self.add_liquid_config = {
            "HCl":{
                'addr': 0x12,
                'pipe_volume': 3.14 * 0.04 * 0.04 * 190,
                'base_speed': 0.0605
            },
            "HCl_wash":{
                'addr': 0x12,
                'pipe_volume': 3.14 * 0.04 * 0.04 * 190,
                'base_speed': 0.0605
            },
            "KMnO4":{
                'addr': 0x13,
                'pipe_volume': 3.14 * 0.04 * 0.04 * 185,
                'base_speed': 0.0632
            },
            "H2O2":{
                'addr': 0x14,
                'pipe_volume': 3.14 * 0.04 * 0.04 * 175,
                'base_speed': 0.0634
            },
            "N2H4":{
                'addr': 0x15,
                'pipe_volume': 3.14 * 0.04 * 0.04 * 250,
                'base_speed': 0.0634
            },
            "CH3CH":{
                'addr': 0x16,
                'pipe_volume': 3.14 * 0.24 * 0.24 * 600,
                'base_speed': 0.07*36
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
            time.sleep(0.1)

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
            time.sleep(0.1)

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
            time.sleep(0.1)

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
            time.sleep(0.1)

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
        base_speed_name = self.add_liquid_config[name]['base_speed']
        speed = base_speed_name * rpm
        tim = (volume + pipe_volume) / speed * 60 # 滴加时间
        Info = {
            '进料液体': name,
            '进料转速': str(rpm) + ' 转/min',
            '进料速度': f'{speed:.3f} ml/min',
            '目标体积': f'{volume:.2f} ml',
            '预期时间': str(int(tim)) + ' s'
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='液料滴加', Info=Info)

        addr = self.add_liquid_config[name]['addr']

        self.log.info(f"滴加液体为{name},体积为{volume}ml,转速为{rpm}rpm，预期需要{tim}s")

        self.writespeed(addr, rpm*10)
        time.sleep(1)
        if name=="KMnO4":
            self.startadd(addr)
            rpm0 = rpm
            speed = base_speed_name * rpm0
            tim = (volume + pipe_volume) / 3.0 / speed * 60 # 滴加时间
            self.event_countdown(addr, tim, name=f'{name}, 第一段', volume=volume/3.0, rpm=rpm0, speed=speed)
            self.writespeed(addr, rpm*10*2)
            rpm0 = rpm * 2
            speed = base_speed_name * rpm0
            tim = (volume + pipe_volume) / 3.0 / speed * 60 # 滴加时间
            self.event_countdown(addr, tim, name=f'{name}, 第二段', volume=volume/3.0, rpm=rpm0, speed=speed)
            self.writespeed(addr, rpm*10*3)
            rpm0 = rpm * 3
            speed = base_speed_name * rpm0
            tim = (volume + pipe_volume) / 3.0 / speed * 60 # 滴加时间
            self.event_countdown(addr, tim, name=f'{name}, 第三段', volume=volume/3.0, rpm=rpm0, speed=speed)
            self.stopadd(addr)
        else:
            self.startadd(addr)
            self.event_countdown(addr, tim, name=name, volume=volume, rpm=rpm, speed=speed)
            self.stopadd(addr)
        if self.reverse == True:
            self.liquid_back(name)

    def liquid_back(self, name, rpm=150):
        addr = self.add_liquid_config[name]['addr']
        # pipe_volume = self.add_liquid_config[name]['pipe_volume']
        if name=='CH3CH':
            pipe_volume = self.add_liquid_config[name]['pipe_volume']
        else:
            pipe_volume = self.pipe_volume_max
        base_speed_name = self.add_liquid_config[name]['base_speed']
        speed = base_speed_name * rpm
        pipe_time = pipe_volume/ speed * 60
        self.writespeed(addr, rpm*10)
        self.writedirection(addr, 0)
        self.startadd(addr)
        self.event_countdown(addr, pipe_time, name=name, volume=pipe_volume, rpm=rpm, directon=0, speed=speed)
        self.stopadd(addr)
        self.writedirection(addr, 1)

    def event_countdown(self, addr, seconds, name:str = '', rpm:float = 0, volume:float = 0, directon:bool = 1, speed:float = 0):
        start_time = time.time()
        end_time = start_time + seconds

        # 用于控制是否停止、暂停的标志
        stop_flag = threading.Event()
        pause_flag = threading.Event() # 用于暂停
        pause_flag.set() # 初始化时设置为非阻塞状态
        is_paused = False
        pause_start_time = 0
        total_pause_duration = 0 # 用于累计总的暂停时间

        # 创建互斥锁，保护串口访问（保护 self.bath 和 self.startadd/stopadd）
        serial_lock = threading.Lock()

        # --- 线程1：用户输入监控线程 ---
        def input_thread():
            nonlocal is_paused, pause_start_time, end_time, total_pause_duration
            while not stop_flag.is_set():
                try:
                    user_input = CommandParser.wait_input("parser", "输入 'q' 跳过, 'p' 暂停, 'c' 继续...")
                    if stop_flag.is_set():
                        break
                    if user_input.lower() == 'q':
                        stop_flag.set()
                        if is_paused: # 如果在暂停时退出，需要恢复事件以结束主循环
                            pause_flag.set()
                        break
                    elif user_input.lower() == 'p' and not is_paused:
                        is_paused = True
                        pause_start_time = time.time()
                        pause_flag.clear() # 清除事件，使主循环的 wait() 阻塞
                        with serial_lock:
                            self.stopadd(addr)
                        print("\n倒计时已暂停。输入 'c' 继续。")
                    elif user_input.lower() == 'c' and is_paused:
                        pause_duration = time.time() - pause_start_time
                        end_time += pause_duration # 将暂停的时间加到结束时间上
                        is_paused = False
                        with serial_lock:
                            self.startadd(addr)
                        pause_flag.set() # 设置事件，使主循环的 wait() 通过
                        print("\n倒计时已恢复。")
                except:
                    break

        # --- 线程2：温度监控线程 (新增) ---
        # 该线程独立运行，不受 pause_flag 影响，只要没停止(stop_flag)就会一直读
        def temp_thread():
            while not stop_flag.is_set():
                if self.bath:
                    # 加锁访问485总线，防止与 input_thread 中的 start/stop 冲突
                    with serial_lock:
                        try:
                            self.bath.read_temp()
                        except Exception as e:
                            # 简单的错误捕获，防止单次读取失败导致线程崩溃
                            print(f"读取温度出错: {e}")
                # 控制读取频率，例如每1秒读一次
                time.sleep(1)

        # 启动输入线程
        input_t = threading.Thread(target=input_thread, daemon=True)
        input_t.start()

        # 启动温度监控线程
        temp_t = threading.Thread(target=temp_thread, daemon=True)
        temp_t.start()

        # --- 主循环：倒计时与显示 ---
        while time.time() < end_time:
            # 检查是否收到停止信号
            if stop_flag.is_set():
                print("\n手动停止计时")
                break

            pause_flag.wait() # 如果 pause_flag 被 clear(), 程序会阻塞在这里 (暂停倒计时)
            # 注意：现在阻塞在这里只会暂停倒计时时间的更新，temp_thread 依然在后台运行

            # 计算剩余时间
            now = time.time()
            remaining_time = end_time - now

            if remaining_time <= 0:
                break

            finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))

            # 使用 \r 回到行首覆盖输出，end='' 避免换行
            print(f"\r剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}", end='', flush=True)

            if directon==0:
                Info = {
                    '回收液体': name,
                    '回收转速': str(rpm) + ' 转/min',
                    '回收速率': str(speed) + ' ml/min',
                    '剩余时间' : str(int(remaining_time)) + ' s',
                    '预计结束时间' : finish_time
                }
                Flowdisplay.update_process_display_dict(Process=None, Action='回收管内液体', Info=Info)
            elif name != '':
                effective_elapsed_time = (now - start_time) - total_pause_duration
                current_volume = volume * effective_elapsed_time / seconds
                Info = {
                    '进料液体': name,
                    '进料转速': str(rpm) + ' 转/min',
                    '进料速率': f'{speed:.3f} ml/min',
                    '已加料体积': f"{current_volume:.2f} ml",
                    '目标体积': f'{volume:.2f} ml',
                    '剩余时间' : str(int(remaining_time)) + ' s',
                    '预计结束时间' : finish_time
                }
                Flowdisplay.update_process_display_dict(Process=None, Action='液料滴加', Info=Info)

            # 短暂等待后继续监控
            time.sleep(1)

        stop_flag.set()  # 设置停止标志，通知输入线程和温度线程结束

        if time.time() >= end_time:
            LogUtils.log.info("时间到")

        total_time = time.time() - start_time
        LogUtils.log.info(f"倒计时结束，总耗时: {int(total_time)} 秒")

        time.sleep(1)


if __name__ == "__main__":
    add_Liquid=PumpGroup('add_Liquid')

    add_Liquid.writespeed(0x12, 100)
    add_Liquid.writespeed(0x13, 100)
    add_Liquid.writespeed(0x14, 100)
    add_Liquid.writespeed(0x15, 100)
    add_Liquid.writespeed(0x16, 100)
    # # add_Liquid.update_data_dict(0x12)

    # add_Liquid.liquid_back('CH3CH', 150)