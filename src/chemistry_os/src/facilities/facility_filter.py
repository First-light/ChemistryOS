import sys




sys.path.append('src/chemistry_os/src')
import time
from time import sleep
from serial.tools import list_ports
import serial
from facility import Facility
from utilities.utility_param import ParamUtils
from utilities.utility_emergency import EmergencyUtils
from facilities.facility_parser import CommandParser
import time


# sudo chmod 666 /dev/ttyUSB0 开串口权限
# ls -l /dev/ttyUSB* 查串口设备

# valve 0方向对应T阀门的左侧
# pump dir 0对应泵的正转

from enum import Enum

class AddressEnum(Enum):
    EMPTY = 0  # 表示地址为空
    SOLVENT = 0x04  # 溶解溶剂
    WATER = 0x02    # 清水清洗液
    ACID = 0x03     # 酸清洗液
    PUMP = 0x01     # 抽滤地址

class Filter(Facility):
    type = "filter"
    default_sub_addresses = {
        "empty": AddressEnum.EMPTY.value,
        "solvent": AddressEnum.SOLVENT.value,
        "water": AddressEnum.WATER.value,
        "acid": AddressEnum.ACID.value,
        "pump": AddressEnum.PUMP.value
    }

    def __init__(self, name: str, com: str = "/dev/ttyUSB0", baudrate: int = 9600, address = 0x50, sub_addresses: dict = default_sub_addresses):
        """
        初始化抽滤装置类
        :param name: 设备名称
        :param com: 串口号
        :param baudrate: 波特率
        :param address: 主控地址，默认0x50
        :param sub_addresses: 下级设备地址字典，包含溶解溶剂、清水清洗液和酸清洗液的地址
        """
        self.com = com
        self.ifconnect = False
        self.baudrate = baudrate
        self.address = address
        self.sub_addresses = sub_addresses
        self.data_dict = {
            "solvent": {"state": 0, "address": AddressEnum.SOLVENT.value,"speed":0,"dir":0},
            "water": { "state": 0, "address": AddressEnum.WATER.value,"speed":0,"dir":0},
            "acid": { "state": 0, "address": AddressEnum.ACID.value,"speed":0,"dir":0},
            "pump": { "state": 0,"address": AddressEnum.PUMP.value,"speed":0,"dir":0},
            "valve_A": {"state": 0},  # 三通阀门
            "valve_B": {"state": 0},  # 三通阀门
            "if_connect":self.ifconnect,
            "com":self.com,
        }
        self.ser = None
        self.liquid_convert_dict = {
            "solvent": {"volume":20,"speed":0,"param":0.007 * 0.1,"extra_volume":0.0},
            "water": {"volume":20,"speed":0,"param":0.007 * 0.1,"extra_volume":0.0},
            "acid": {"volume":20,"speed":0,"param":0.007 * 0.1,"extra_volume":0.0},
            "pump": {"volume":20,"speed":0,"param":0.007 * 0.1,"extra_volume":0.0},
        }#extra_volume mL
        super().__init__(name, Filter.type)
        self.connect()
        self.pump_init()  # 初始化蠕动泵
        self.init_dict = ParamUtils.get_init_params(self)

    def cmd_init(self):
        """
        注册指令
        """
        self.parser.register("test", self.test, {}, "send empty command")
        self.parser.register("pump", self.pump_control_name, {
                             "name": "empty", "state": 0}, "control pump on/off by name")
        self.parser.register("dir", self.set_pump_dir_name, {
                             "name": "empty", "direction": 0}, "set pump direction by name")
        self.parser.register("speed", self.set_pump_speed_name, {
                             "name": "empty", "speed": 0}, "set pump speed by name")
        self.parser.register("valve", self.valve_A_control, {
                             "state": 0}, "control valve on/off")
        
        self.parser.register("query", self.pump_query, {
                             "address": self.sub_addresses["solvent"]}, "query pump status")
        self.parser.register("setaddr", self.set_pump_address, {
                             "old_address": self.sub_addresses["solvent"], "new_address": AddressEnum.EMPTY.value}, "set pump address")
        self.parser.register("setvolume", self.liquid_set_volume_name, {
                             "name": "", "volume": 0.0}, "set pump volume")
        
        self.parser.register("init", self.pump_init, {}, "initialize pump")
        self.parser.register("A", self.filter_process_A, {}, "start filter process A")
        self.parser.register("B", self.filter_process_B, {}, "start filter process B")
        self.parser.register("C", self.filter_process_C, {}, "start filter process C")
        self.parser.register("data", self.print_data, {}, "check data")
        self.parser.register("load", self.liquid_load, {
                             "name": "empty"}, "load liquid into pump by name")

    def cmd_error_handing(self):
        self.pump_control_name("solvent",0)
        self.pump_control_name("acid",0)
        self.pump_control_name("water",0)
        self.pump_control_name("pump",0)
        self.valve_A_control(0)
        self.valve_B_control(0)
        self.facility_emergency = True

    def cmd_stop_handing(self):
        self.pump_control_name("solvent",0)
        self.pump_control_name("acid",0)
        self.pump_control_name("water",0)
        self.pump_control_name("pump",0)
        self.valve_A_control(0)
        self.valve_B_control(0)
        self.facility_emergency = True


    def cmd_reset(self):#从error/stop恢复idle的状态
        self.facility_emergency = False
        pass

    def data_dict_update(self):
        self.data_dict.update({
            "if_connect":self.ifconnect,
            "com":self.com,
        })

    def filter_process_A(self):
        """
        抽滤过程A
        """
        self.log.info("开始过程A")
        self.valve_A_control(0)  # 打开三通阀门
        out = True
        while out == True:
            self.log.info("抽滤30s")
            self.pump_control_name("pump", 1)# 泵启动
            time.sleep(30)  
            self.pump_control_name("pump", 0)
            if CommandParser.wait_input("parser","是否继续抽滤？(y/n): ").strip().lower() is not 'y':
                out = False

        self.valve_A_control(0)  # 
        self.valve_B_control(0)  # 
        self.log.info("等待10s")
        time.sleep(10)  # 泵启动
        self.log.info("抽滤过程A完成")

    def filter_process_B(self):
        """
        抽滤过程B
        """
        self.log.info("开始过程B")
        self.valve_B_control(0)  # 打开三通阀门
        # self.pump_control_name("acid", 1)
        # time.sleep(20)  # 泵启动
        # self.pump_control_name("acid", 0)
        # self.valve_B_control(1)  # 打开三通阀门
        # self.pump_control_name("water", 1)
        # time.sleep(20)  # 泵启动
        # self.pump_control_name("water", 0)
        out = True
        while out == True:
            sec = self.liquid_convert_name("acid")
            self.log.info(f"酸洗{sec:.3f}s")
            self.pump_control_name("acid", 1)
            time.sleep(sec)
            self.pump_control_name("acid", 0)
            if CommandParser.wait_input("parser","是否继续酸洗？(y/n): ").strip().lower() != 'y':
                out = False
        self.valve_B_control(1)
        out = True
        while out == True:
            sec = self.liquid_convert_name("water")
            self.log.info(f"清水清洗{sec:.3f}s")
            self.pump_control_name("water", 1)
            time.sleep(sec)
            self.pump_control_name("water", 0)
            if CommandParser.wait_input("parser","是否继续清水清洗？(y/n): ").strip().lower() != 'y':
                out = False
        self.valve_A_control(0)  # 打开三通阀门
        self.valve_B_control(0)  # 
        self.log.info("抽滤过程B完成")

    def filter_process_C(self):
        """
        抽滤过程C
        """
        self.log.info("开始过程C")
        self.valve_A_control(1)  # 
        # self.pump_control_name("solvent", 1)
        # time.sleep(20)  # 泵启动
        # self.pump_control_name("solvent", 0)
        out = True
        while out == True:
            sec = self.liquid_convert_name("solvent")
            self.log.info(f"溶剂{sec:.3f}s")
            self.pump_control_name("solvent", 1)
            time.sleep(sec)
            self.pump_control_name("solvent", 0)
            if CommandParser.wait_input("parser","是否继续溶剂？(y/n): ").strip().lower() is not 'y':
                out = False
        self.valve_A_control(0)  # 打开三通阀门
        self.valve_B_control(0)  # 



    def pump_init(self):
        """
        初始化蠕动泵
        """
        self.set_pump_dir_name("pump", 0),
        self.set_pump_speed_name("pump", 800),
        self.set_pump_dir_name("water", 1),
        self.set_pump_speed_name("water", 800),
        self.set_pump_dir_name("acid", 1),
        self.set_pump_speed_name("acid", 800),
        self.set_pump_dir_name("solvent", 1),
        self.set_pump_speed_name("solvent", 500),

    def connect(self):
        """
        连接设备
        """
        try:
            self.ser = serial.Serial(self.com, self.baudrate, timeout=1)
            self.log.info(f"{self.name} 485协议初始化完成,端口:{self.com}")
            self.ifconnect = True
            self.log.info(f"测试地址连接 {self.address}")
            ret = self.test()  # 测试连接
            if ret:
                self.log.info(f"{self.name} 连接成功")
            else:
                self.log.warning(f"{self.name} 连接失败")
                self.ifconnect = False
        except Exception as e:
            self.log.warning(f"连接失败: {str(e)}")
            self.ifconnect = False

    def pump_control_name(self, name: str, state: int):
        """
        控制蠕动泵开关
        :param name: 蠕动泵名称
        :param state: 1=打开, 0=关闭
        """
        result = None
        if name not in self.sub_addresses:
            self.log.warning(f"无效的蠕动泵名称: {name}")
        else:
            address = self.sub_addresses[name]
            old_state = self.data_dict[name]["state"]
            if not old_state == state:
                self.data_dict[name]["state"] = state
                result = self.pump_control(address, state)
        return result

    def pump_run_time(self, name: str, sec: float):
        """
        控制蠕动泵开关
        :param name: 蠕动泵名称
        :param state: 1=打开, 0=关闭
        """
        self.pump_control_name(name,state=1)
        time.sleep(sec)
        self.pump_control_name(name,state=0)
    
    def liquid_convert(self,volume:float, speed:float,param:float,extra_volume:float) -> float:
        result = 10.0
        return result


    def liquid_convert_name(self,name:str)->float:
        result = None
        if name not in self.liquid_convert_dict:
            self.log.warning(f"无效的蠕动泵名称: {name}")
        else:
            speed = self.liquid_convert_dict[name]["speed"]
            param = self.liquid_convert_dict[name]["param"]
            volume = self.liquid_convert_dict[name]["volume"]
            extra_volume = self.liquid_convert_dict[name]["extra_volume"]
            convert_sec  = self.liquid_convert(volume, speed,param,extra_volume)
            result_sec = min(convert_sec,240.0)
            result = result_sec
        return result

    def liquid_set_volume_name(self,name:str,volume:float):
        result = True
        if name not in self.liquid_convert_dict:
            self.log.warning(f"无效的蠕动泵名称: {name}")
            result = False
        else:
            self.liquid_convert_dict[name]["volume"] = volume
            self.log.warning(f"蠕动泵：{name} 已设置进料：{volume} mL")
        return result

    def liquid_load(self, name: str):
        """
        加载液体到蠕动泵
        :param name: 蠕动泵名称
        """
        self.log.info(f"{name}预装载液体")
        self.set_pump_speed_name(name,300,if_save=False)
        CommandParser.wait_input("parser","ok?")
        self.pump_control_name(name, 1)
        CommandParser.wait_input("parser","over?")
        self.pump_control_name(name, 0)
        self.reset_pump_speed_by_dict(name)  # 重置蠕动泵速度为字典中的值
        self.log.info(f"{name}预装载结束")
        

    def pump_control(self, address: int, state: int):
        """
        控制蠕动泵开关
        :param address: 蠕动泵设备地址
        :param state: 1=打开, 0=关闭
        """
        result = None
        if address == self.sub_addresses["empty"]:
            self.log.warning("地址为空，无法发送指令")
        else:
            state_int = int(state)
            if state_int not in [0, 1]:
                self.log.warning("无效的阀门状态，请输入 1 或 0")
            else:
                state_byte = state_int.to_bytes(1, byteorder='big')
                command = [self.address, 0x01, address, 0x00, state_byte[0], 0x55]
                result = self.send_command(command)
        return result

    def set_pump_address(self, old_address: int, new_address: int):
        """
        设置蠕动泵的新地址
        :param old_address: 当前设备地址
        :param new_address: 新地址 (0x00 表示不设置新地址)
        """
        result = False
        if new_address == self.sub_addresses["empty"]:
            self.log.warning("新地址无效，未进行设置")
        else:
            command = [self.address, 0x04, old_address, 0x00, new_address, 0x55]
            response = self.send_command(command)

            # 如果设置成功，更新类中的 sub_addresses
            if response:
                for key, addr in self.sub_addresses.items():
                    if addr == old_address:
                        self.sub_addresses[key] = new_address
                        self.log.info(f"{key} 的地址已更新为: {hex(new_address)}")
                        break
                result = True
            else:
                self.log.warning("设置蠕动泵地址失败")
        return result

    def send_command(self, command: list):
        """
        发送指令到设备
        :param command: 指令列表
        """
        command_t = bytearray(command)
        if not self.ifconnect:
            self.log.warning(f"发送指令失败 {command_t} 设备未连接，请检查连接")
            return None
        elif self.facility_emergency:
            self.log.warning(f"发送指令失败 {command_t} 设备处于紧急状态")
            return None
        wait_time = 2.0
        try:
            with serial.Serial(port=self.com, baudrate=self.baudrate, timeout=1, stopbits=2) as ser:
                # self.log.info("成功连接")
                ser.write(command_t)
                self.log.info(f"发送指令: {command_t}")
                start_time = time.time()
                while True:
                    sleep(0.001)
                    if ser.in_waiting > 0:
                        # 读取设备响应
                        response = ser.read(ser.in_waiting)
                        response_str = response.decode('utf-8', errors='ignore')
                        self.log.info(f"设备响应: {response}")

                        time.sleep(0.1)  # 确保串口数据发送完成
                        return response_str
                    if time.time() - start_time > wait_time:
                        # 超过等待时间，认为超时
                        self.log.error(f"发送指令失败{command_t}: 超时未收到响应")
                        return None
           
        except Exception as e:
            self.log.warning(f"发送指令中断: {str(e)}")
            return None

    def test(self):
        """
        空指令，用于回环测试
        """
        command = [self.address, 0x00, 0x55, 0x55, 0x55, 0x55]
        return self.send_command(command)

    def set_pump_dir_name(self, name: str,direction: int):
        """
        设置蠕动泵方向
        :param name: 蠕动泵名称
        :param direction: 方向，1=正转, 0=反转
        """
        result = None
        if name not in self.sub_addresses:
            self.log.warning(f"无效的蠕动泵名称: {name}")
        else:
            address = self.sub_addresses[name]
            self.data_dict[name]["dir"] = direction
            result = self.set_pump_direction(address, direction)
        return result
        
    def set_pump_speed_name(self, name: str, speed: int,if_save = True):
        """
        设置蠕动泵速度
        :param name: 蠕动泵名称
        :param speed: 速度值 (0-65535)
        """
        result = None
        if name not in self.sub_addresses:
            self.log.warning(f"无效的蠕动泵名称: {name}")
        else:
            address = self.sub_addresses[name]
            if name in self.liquid_convert_dict and if_save:
                self.liquid_convert_dict[name]["speed"] = speed
                self.data_dict[name]["speed"] = speed
            result = self.set_pump_speed(address, speed)
        return result

    def reset_pump_speed_by_dict(self, name: str):
        """
        重置蠕动泵速度为字典中的值
        :param name: 蠕动泵名称
        """
        result = None
        if name not in self.sub_addresses:
            self.log.warning(f"无效的蠕动泵名称: {name}")
        else:
            address = self.sub_addresses[name]
            speed = self.liquid_convert_dict[name]["speed"]
            self.data_dict[name]["speed"] = speed
            result = self.set_pump_speed(address, speed)
        return result

    def set_pump_direction(self, address: int, direction: int):
        """
        设置蠕动泵方向
        :param address: 蠕动泵设备地址
        :param direction: 方向，1=正转, 0=反转
        """
        result = None
        direction_int = int(direction)
        if direction_int not in [0, 1]:
            self.log.info("无效的方向，请输入 1 或 0")
        else:
            direction_byte = direction_int.to_bytes(1, byteorder='big')
            command = [self.address, 0x02, address, 0x00, direction_byte[0], 0x55]
            result = self.send_command(command)
        return result

    def set_pump_speed(self, address: int, speed: int):
        """
        设置蠕动泵速度
        :param address: 蠕动泵设备地址
        :param speed: 速度值 (0-65535)
        """
        result = None
        speed = int(speed)
        if speed < 0 or speed > 65535:
            self.log.warning("速度值超出范围，请输入 0-65535")
        else:
            high_byte = (speed >> 8) & 0xFF
            low_byte = speed & 0xFF
            command = [self.address, 0x03, address, high_byte, low_byte, 0x55]
            result = self.send_command(command)
        return result

    def valve_A_control(self, state: int):
        """
        控制靠近电源口侧三通阀门开关（一般是抽滤段）
        :param state: 1=打开, 0=关闭
        1 = 蠕动泵端关
        0 = 气泵端关
        """
        result = None
        state_int = int(state)
        if state_int not in [0, 1]:
            self.log.warning("无效的阀门状态，请输入 1 或 0")
        else:
            state_byte = state_int.to_bytes(1, byteorder='big')
            command = [self.address, 0x05, state_byte[0], 0x55, 0x55, 0x55]
            self.data_dict["valve_A"]["state"] = state
            result = self.send_command(command)
        return result

    def valve_B_control(self, state: int):
        """
        控制阀门B开关
        :param state: 1=打开, 0=关闭
        """
        result = True
        state_int = int(state)
        if state_int not in [0, 1]:
            self.log.warning("无效的阀门状态，请输入 1 或 0")
            result = False
        else:
            state_byte = state_int.to_bytes(1, byteorder='big')
            command = [self.address, 0x06, state_byte[0], 0x55, 0x55, 0x55]
            self.send_command(command)
            self.data_dict["valve_B"]["state"] = state
        return result

    def pump_query(self, address: int):
        """
        查询蠕动泵开关、方向、速度
        :param address: 蠕动泵设备地址
        """
        # command = [self.address, 0x09, address, 0x00, 0x00, 0x55]
        command = [0x50,0x07,0x55,0x55,0x55,0x55]
        return self.send_command(command)
    
    def print_data(self):
        """
        检查数据
        """
        print(f"{self.sub_addresses} 数据检查")
        print(f"{self.liquid_convert_dict} 数据检查")
