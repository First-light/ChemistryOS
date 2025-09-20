import sys
sys.path.append('src/chemistry_os/src')
import serial
import time
from facility import Facility
from utilities.events import event_countdown
from facilities.flowdisplay import Flowdisplay
from utilities.utility_param import ParamUtils

class Thermometer(Facility):

    usb_name='/dev/ttyUSB_tem'
    type='thermometer'

    def __init__(self, name: str):
        super().__init__(name, Thermometer.type)
        self.init_dict = ParamUtils.get_init_params(self)
        self.data_dict = {
            "temperature": '--'
        }
        self.read_temp()
        self.update_data_dict(temperature='--')
    
    def cmd_error_handing(self):
        pass

    def cmd_reset(self):
        pass

    def cmd_stop_handing(self):
        pass

    def update_data_dict(self, temperature=None):
        """
        更新数据字典
        """
        if temperature is not None:
            self.data_dict['temperature'] = temperature

    def cmd_init(self):
        """
        注册指令
        """
        self.parser.register("init", self.cmd_init, {}, "初始化温度计")

    def extract_and_convert_temperature(self, hex_data):
        # 确保传入的数据是bytes类型
        if not isinstance(hex_data, bytes) or len(hex_data) != 7:
            raise ValueError("Invalid bytes data provided")
        
        # 使用struct解包为有符号整数
        result = int.from_bytes(hex_data[3:5], byteorder='big', signed=False)

        return result/10

    def read_temp(self):
        command = bytearray([0x00, 0x03, 0x00, 0x00, 0x00, 0x01, 0x85, 0xDB])
        try:
            with serial.Serial(self.usb_name, 9600) as ser:
                ser.write(command)
                time.sleep(0.05)
                response = ser.read(ser.in_waiting)
                result = self.extract_and_convert_temperature(response)
                # print("Temperature:", result)
                self.update_data_dict(temperature=result)
        except Exception as e:
            print("Error:", str(e))

if __name__ == "__main__":
    thermometer = Thermometer("thermometer")
    while 1:
        thermometer.read_temp()
        print(thermometer.data_dict['temperature'])