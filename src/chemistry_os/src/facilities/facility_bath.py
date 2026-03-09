import sys
from enum import Enum

sys.path.append('src/chemistry_os/src')
from facilities.facility_parser import CommandParser
from facility import Facility
from structs import FacilityState
from time import sleep
from serial.tools import list_ports
import serial
import time
import threading
import sys
import select
from pymodbus.client import ModbusSerialClient
from facilities.flowdisplay import Flowdisplay
from utilities.utility_param import ParamUtils

class Bath(Facility):
    type = "bath"
    bath_com = '/dev/ttyUSB_485'
    bath_addr = 0x11
    TMP_ERROR = 999 # 温度读取错误标志

    def __init__(self,name:str):
        
        super().__init__(name,self.type)
        self.modbus_client = ModbusSerialClient(port=self.bath_com, baudrate=9600)
        self.init_dict = ParamUtils.get_init_params(self)
        # 初始化水浴锅各项参数字典
        self.data_dict = {
            'power': 0,      # 电源状态
            'cold': 0,       # 制冷状态
            'hot': 0,        # 加热状态
            'mix': 0,        # 搅拌状态
            'circle': 0,     # 循环状态
            'temp': 0,       # 当前温度
            'temp_set': 0,   # 设定温度
        }
        self.init_data_dict()
        # self.modbus_client.connect()
        # 连接期间会独占串口设备

    def update_data_dict(self, power = None, cold = None, hot = None, mix = None, circle = None, temp = None, temp_set = None):
        if power:
            self.data_dict['power'] = power
        if cold:
            self.data_dict['cold'] = cold
        if hot:
            self.data_dict['hot'] = hot
        if mix:
            self.data_dict['mix'] = mix
        if circle:
            self.data_dict['circle'] = circle
        if temp:
            self.data_dict['temp'] = temp
        if temp_set:
            self.data_dict['temp_set'] = temp_set

    def init_data_dict(self):
        now_tmp = self.read_temp()
        while now_tmp == self.TMP_ERROR:
            now_tmp = self.read_temp()
        now_set_tmp = self.read_temp_set()
        while now_set_tmp == self.TMP_ERROR:
            now_set_tmp = self.read_temp_set()
        

    def output(self,param1,param2):
        self.log.info("output:",param1,param2)

    def cmd_init(self):
        self.parser.register("output", self.output, {"param1": 0, "param2": 1}, "output test")
        # interactable_writetmp cold_ctr
        self.parser.register("write_temp_control", self.interactable_writetmp, {"tmp": 25}, "水浴锅控温")
        self.parser.register("write_temp", self.write_temp, {"tmp": 25}, "水浴锅写入温度")
        self.parser.register("cold_ctr", self.cold_ctr, {"on": 0}, "制冷开启or关闭")
        self.parser.register("hot_ctr", self.hot_ctr, {"on": 0}, "制热开启or关闭")

    def cmd_error_handing(self):
        self.power_ctr(on=0)

    def cmd_stop_handing(self):
        self.power_ctr(on=0)
        
    def cmd_reset(self):#从error/stop恢复idle的状态
        pass

    def listen(self):
        while True:
            if self.state == FacilityState.ERROR:
                break
            if self.state == FacilityState.STOP:
                break
            sleep(0.005)

    class ControlBit(Enum):
        """
        水浴锅控制寄存器各位的定义和位位置。
        根据提供的表格，定义了从第0位到第8位的控制功能。
        第9位到第15位为预留或未使用。
        """
        BUZZER_MUTE =    0x0001  # 第0位: 蜂鸣器/消音键 (BCK)
        POWER =          0x0002  # 第1位: 电源键 (PWR)
        CHANNEL_SWITCH = 0x0004  # 第2位: 主控与辅控温度通道切换键 (RSK)
        HEATING =        0x0008  # 第3位: 加热键 (HTK)
        COOLING =        0x0010  # 第4位: 制冷键 (CLK)
        CIRCULATION =    0x0020  # 第5位: 循环键 (LPK)
        STIRRING =       0x0040  # 第6位: 搅拌键 (SRK)
        LIQUID_ADDING =  0x0080  # 第7位: 加液键 (ALK)
        AUTO_TUNING =    0x0100  # 第8位: 温度自整定开关 (AT)

    def get_control_status(self, close_serial=True) -> int:
        """
        此为水浴锅状态查询函数
        接受字符串作为查询的动作类型
        返回查询结果
        """
        ERROR = -1

        try:
            if not self.modbus_client.connect():
                return ERROR

            result = self.modbus_client.read_holding_registers(7, slave=self.bath_addr)

            if result.isError():
                return ERROR

            return result.registers[0]
        finally:
            if close_serial:
                self.modbus_client.close()

    def _common_ctr(self, on, control_bit:ControlBit, debug_str, close_serial):
        ERROR = -1
        retries = 3
        last_exception = None

        on = bool(on)
        while retries > 0:
            try:
                if not self.modbus_client.connect():
                    self.log.warning("Modbus 连接失败，正在重试...")
                    raise ConnectionError("Modbus connection failed")

                status = self.get_control_status(close_serial=False)
                if status == ERROR:
                    self.log.warning("获取控制状态失败，正在重试...")
                    raise IOError("Failed to get control status")

                status_wanted = bool(status & control_bit.value)
                if status_wanted == on:
                    self.log.info(debug_str + '状态不变')
                    return
                elif status and not on:
                    self.log.info(debug_str + '允许关闭')
                else:
                    self.log.info(debug_str + '允许开启')

                result = self.modbus_client.write_register(7, control_bit.value, slave=self.bath_addr)
                if result.isError():
                    print("写入寄存器失败，正在重试...")
                    raise IOError("Failed to write register")
                
                return # 操作成功，退出函数
            except Exception as e:
                last_exception = e
                retries -= 1
                print(f"操作失败: {e}。剩余重试次数: {retries}")
                time.sleep(1) # 等待1秒后重试
            finally:
                if self.modbus_client.is_socket_open():
                    self.modbus_client.close()
        
        self.log.warning(f"重试多次后操作仍然失败: {last_exception}")
        # 在 finally 块之外处理 close_serial，因为循环内的 finally 会多次关闭
        if close_serial and self.modbus_client.is_socket_open():
            self.modbus_client.close()
        return ERROR

    def power_ctr(self, on, close_serial=True):
        """
        此为电源状态控制函数
        接受整数作为控制器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        self.update_data_dict(power=on)
        return self._common_ctr(on,
                                Bath.ControlBit.POWER,
                               '开机',
                                close_serial)
    
    def cold_ctr(self, on, close_serial=True):
        """
        此为制冷状态控制函数
        接受整数作为控制器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        self.update_data_dict(cold=on)
        return self._common_ctr(on,
                                Bath.ControlBit.COOLING,
                               '制冷',
                                close_serial)

    def hot_ctr(self, on, close_serial=True):
        """
        此为加热状态控制函数
        接受整数作为控制器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        self.update_data_dict(hot=on)
        return self._common_ctr(on,
                                Bath.ControlBit.HEATING,
                               '加热',
                                close_serial)

    def mix_ctr(self, on, close_serial=True):
        """
        此为搅拌器控制函数
        接受整数作为控制器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        self.update_data_dict(mix=on)
        return self._common_ctr(on,
                                Bath.ControlBit.STIRRING,
                               '搅拌器',
                                close_serial)

    def circle_ctr(self, on, close_serial=True):
        """
        此为循环系统控制函数
        接受整数作为控制器的开关，on=1为开，on=0为关，若状态不变则不进行操作
        """
        self.update_data_dict(circle=on)
        return self._common_ctr(on,
                                Bath.ControlBit.CIRCULATION,
                               '循环系统',
                                close_serial)

    def write_temp(self, temp, close_serial=True):
        ERROR = -1
        OVERRANGE = -2
        retries = 3
        last_exception = None

        if temp > 40:
            self.log.warning("温度过高！")
            return OVERRANGE
        if temp < -20:
            self.log.warning("温度过低！")
            return OVERRANGE

        while retries > 0:
            try:
                if not self.modbus_client.connect():
                    raise ConnectionError("Modbus connection failed")

                val_to_write = int(temp * 10)
                if val_to_write < 0:
                    val_to_write += 0x10000

                result = self.modbus_client.write_register(2, val_to_write, slave=self.bath_addr)

                if result.isError():
                    print("写入寄存器失败，正在重试...")
                    raise IOError("Failed to write register")
                
                self.update_data_dict(temp_set=temp)
                self.log.info('写入温度成功')
                return  # 成功，直接返回
            except Exception as e:
                last_exception = e
                retries -= 1
                print(f"写入温度失败: {e}。剩余重试次数: {retries}")
                time.sleep(1)
            finally:
                if self.modbus_client.is_socket_open():
                    self.modbus_client.close()

        self.log.warning(f"重试多次后写入温度仍然失败: {last_exception}")
        if close_serial and self.modbus_client.is_socket_open():
            self.modbus_client.close()
        return ERROR

    def read_working(self, close_serial=True):
        """
        读取是否正在加热或制冷
        """
        ERROR=-1
        try:
            if not self.modbus_client.connect():
                return ERROR

            result = self.modbus_client.read_holding_registers(8, slave=self.bath_addr)

            if result.isError():
                return ERROR

            status = result.registers[0]
            status_cold = bool(status & 0x0080)
            status_heat = bool(status & 0x0001)
            self.log.info('是否正在加热：', status_heat)
            self.log.info('是否正在制冷:', status_cold)
        finally:
            if close_serial:
                self.modbus_client.close()

    def read_temp_set(self, close_serial=True):
        """
        读取设置的工作温度
        """

        try:
            if not self.modbus_client.connect():
                return self.TMP_ERROR

            result = self.modbus_client.read_holding_registers(2, slave=self.bath_addr)

            if result.isError():
                return self.TMP_ERROR

            temp_set = result.registers[0]
            # 检查最高位是否为1（负数）
            if temp_set & 0x8000:
                # 如果是负数，进行二进制补码转换
                temp_set -= 0x10000

            temp_set /= 10.0
            self.update_data_dict(temp_set=temp_set)
            return temp_set
        except Exception as e:
            # print(f"读取设定温度出错: {e}")
            return self.TMP_ERROR
        finally:
            if close_serial:
                self.modbus_client.close()

    def read_temp(self, close_serial=True):
        """
        读取当前温度
        """
        try:
            if not self.modbus_client.connect():
                return self.TMP_ERROR

            result = self.modbus_client.read_holding_registers(0, slave=self.bath_addr)

            if result.isError():
                return self.TMP_ERROR

            temp = result.registers[0]
            # 检查最高位是否为1（负数）
            if temp & 0x8000:
                # 如果是负数，进行二进制补码转换
                temp -= 0x10000

            temp /= 10.0
            self.update_data_dict(temp=temp)
            return temp
        
        except Exception as e:
            # print(f"读取温度出错: {e}")
            return self.TMP_ERROR
        
        finally:
            if close_serial:
                self.modbus_client.close()

    def interactable_writetmp(self, tmp, close_hot = 1):
        self.hot_ctr(1)
        Info = {
                '控制温度': str(tmp) + ' ℃',
                '当前温度': '',
                '剩余时间': '',
            }
        Flowdisplay.update_process_display_dict(Process=None, Action='水浴锅控温', Info=Info)

        now_tmp = self.read_temp()
        while now_tmp == self.TMP_ERROR:
            now_tmp = self.read_temp()  # 读取失败时保持上次温度值
        start_tmp = now_tmp + 0.001
        start_time = time.time()
        self.write_temp(tmp)
        self.log.info('控温中...')
        
        # 用于控制是否停止的标志
        stop_flag = threading.Event()
        
        def input_thread():
            while not stop_flag.is_set():
                try:
                    user_input = CommandParser.wait_input("parser", "输入 'q' 跳过控温...")
                    if stop_flag.is_set():
                        break
                    if user_input.lower() == 'q':
                        stop_flag.set()
                        break
                except:
                    break
        
        # 启动输入线程
        input_t = threading.Thread(target=input_thread, daemon=True)
        input_t.start()

        tmp_offset = 3
        
        while now_tmp > tmp + tmp_offset or now_tmp < tmp - tmp_offset:
            # 检查是否收到停止信号
            if stop_flag.is_set():
                self.log.info("手动停止控温")
                break
                
            bias = tmp_offset if abs(tmp + tmp_offset - start_tmp) < abs(tmp - tmp_offset - start_tmp) else -tmp_offset
            remaining_time = (tmp - now_tmp + bias) / ((now_tmp - start_tmp) / (time.time() - start_time))
            if remaining_time < 0:
                remaining_time *= -1
            
            finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + remaining_time))
            
            # 使用 \r 回到行首覆盖输出，end='' 避免换行
            print(f"\r当前温度为:{now_tmp},指定温度{tmp}，继续控温，预计剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}", end='', flush=True)
            
            Info = {
                '控制温度': str(tmp) + ' ℃',
                '当前温度': str(now_tmp) + ' ℃',
                '预计剩余时间': str(int(remaining_time)) + ' s'
            }
            Flowdisplay.update_process_display_dict(Process=None, Action='水浴锅控温', Info=Info)
            
            # 短暂等待后继续监控
            time.sleep(1)
            last_tmp = now_tmp
            now_tmp = self.read_temp()
            if now_tmp == self.TMP_ERROR:
                now_tmp = last_tmp  # 读取失败时保持上次温度值
        
        stop_flag.set()  # 确保输入线程结束
        self.log.info(f"到达指定温度附近，当前温度为{now_tmp}，共耗时{time.time() - start_time}秒")

        time.sleep(1)

        if close_hot:
            self.hot_ctr(0)
            self.log.info("加热关闭")

if __name__ == '__main__':
    bath = Bath('bath')

    # print(bath.get_control_status())
    # bath.write_temp(-5)
    # while 1:
    #     bath.power_ctr(1)
    # bath.hot_ctr(1)
    # bath.cold_ctr(1)
    # bath.mix_ctr(1)
    # bath.circle_ctr(1)
    while 1:
        bath.write_temp(25)
