import sys
from enum import Enum
from typing import Optional

sys.path.append('src/chemistry_os/src')
from facilities.facility_parser import CommandParser
from facility import Facility
from structs import FacilityState
from time import sleep
import time
import threading
from pymodbus.client import ModbusSerialClient
from facilities.flowdisplay import Flowdisplay
from utilities.utility_param import ParamUtils


class Scrape(Facility):
    type = "scrape"
    scrape_com = '/dev/ttyUSB_485'
    scrape_addr = 0x51
    channels = 2

    def __init__(self, name: str, com: str = scrape_com, addr: int = scrape_addr, baudrate: int = 9600):
        super().__init__(name, self.type)
        self.modbus_client = ModbusSerialClient(port=com, baudrate=baudrate)
        self.addr = addr
        self.init_dict = ParamUtils.get_init_params(self)

        self.data_dict = {
            "channel_0_status": False,
            "channel_1_status": False,
        }
        self.init_data_dict()
        # self.modbus_client.connect()
        # 连接期间会独占串口设备

    def update_data_dict(self):
        socket_status = self.modbus_client.is_socket_open()

        self.modbus_client.connect()
        for i in range(self.channels):
            self.data_dict[f'channel_{i}_status'] = self.read_channel(i)

        if not socket_status:
            self.modbus_client.close()

    def init_data_dict(self):
        self.update_data_dict()

    def output(self, param1, param2):
        self.log.info("output:", param1, param2)

    def cmd_init(self):
        # TODO
        pass

    def cmd_error_handing(self):
        # TODO
        pass

    def cmd_stop_handing(self):
        # TODO
        pass

    def cmd_reset(self):  # 从error/stop恢复idle的状态
        pass

    def listen(self):
        while True:
            if self.state == FacilityState.ERROR:
                break
            if self.state == FacilityState.STOP:
                break
            sleep(0.005)

    @staticmethod
    def setup_controller(com: str, prev_addr: int, new_addr:int, prev_baudrate: int = 38400, new_baudrate:int = 9600):
        valid_baudrates = (4800, 9600, 14400, 19200, 38400, 56000, 57600, 115200)
        if new_baudrate not in valid_baudrates:
            raise ValueError(f"Invalid baudrate: {new_baudrate}. Valid options are: {valid_baudrates}")
        if not (1 <= new_addr <= 247):
            raise ValueError("Address must be between 1 and 247")

        baudrate_index = valid_baudrates.index(new_baudrate)

        with ModbusSerialClient(port=com, baudrate=prev_baudrate) as client:
            client.write_register(0x32, new_addr, slave=prev_addr)
            client.write_register(0x33, baudrate_index, slave=prev_addr)

        print("Controller setup complete.")
        print("Please restart the device to apply new settings.")

    def read_channel(self, channel: int) -> Optional[bool]:
        if not (0 <= channel < self.channels):
            raise ValueError(f"Channel must between 0 and {self.channels - 1}")

        result = self.modbus_client.read_coils(channel, count=1, slave=self.addr)
        if result.isError():
            self.log.error(f"Failed to read channel {channel}")
            return None
        return result.bits[0]

    def write_channel(self, channel: int, value: bool) -> bool:
        if not (0 <= channel < self.channels):
            raise ValueError(f"Channel must between 0 and {self.channels - 1}")

        result = self.modbus_client.write_coil(channel, value, slave=self.addr)
        if result.isError():
            self.log.error(f"Failed to write channel {channel} with value {value}")
            return False
        return True

    def __enter__(self):
        self.modbus_client.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.modbus_client.close()


if __name__ == '__main__':
    addr = 0x51
    baudrate = 9600
    # Scrape.setup_controller('/dev/ttyUSB0', prev_addr=0x01, new_addr=addr, prev_baudrate=38400, new_baudrate=baudrate)
    scrape = Scrape("scrape", baudrate=baudrate, com='/dev/ttyUSB0', addr=addr)
    input('Press Enter to start...')

    with scrape:
        scrape.write_channel(0, False)
        scrape.write_channel(1, False)
        time.sleep(1)
        for _ in range(10):
            channel_0_status = scrape.read_channel(0)
            print(f'Channel 0 Status: {channel_0_status}')
            write_result = scrape.write_channel(0, not channel_0_status)
            print(f'Write Channel 0 Result: {write_result}')
            time.sleep(0.5)

        for _ in range(10):
            channel_1_status = scrape.read_channel(1)
            print(f'Channel 1 Status: {channel_1_status}')
            write_result = scrape.write_channel(1, not channel_1_status)
            print(f'Write Channel 1 Result: {write_result}')
            time.sleep(0.5)

        # results = scrape.modbus_client.read_coils(0x0000, slave=addr)
        # print(f'Coils: {results.bits}, Length: {len(results.bits)}')
        # results = scrape.modbus_client.write_coil(0x0000, True, slave=addr)
        # print(f'Write Coil Result: {results}')
        # results = scrape.modbus_client.read_coils(0x0000, slave=addr)
        # print(f'Coils: {results.bits}, Length: {len(results.bits)}')
        #
        # results = scrape.modbus_client.write_register(0x0096, 1, slave=addr)
        # print(f'Write Register Result: {results}')
        #
        #
        # previous_result: bool = scrape.modbus_client.read_discrete_inputs(0x0000, slave=addr).bits[0]
        # while True:
        #     result = scrape.modbus_client.read_discrete_inputs(0x0000, slave=addr).bits[0]
        #     if result != previous_result:
        #         print(f'Coil 0x0000 changed to: {result}')
        #         previous_result = result
        #         print(f'{time.time()}')
        #
        #     time.sleep(0.005)



        # results = scrape.modbus_client.read_coils(0x0001, slave=addr)
        # print(f'Coils: {results.bits}, Length: {len(results.bits)}')
        # results = scrape.modbus_client.write_register(0x0002, 1, slave=addr)
        # print(f'Write Register Result: {results}')
        # results = scrape.modbus_client.read_coils(0x0001, slave=addr)
        # print(f'Coils: {results.bits}, Length: {len(results.bits)}')
        # time.sleep(1.5)
        # results = scrape.modbus_client.read_coils(0x0001, slave=addr)
        # print(f'Coils: {results.bits}, Length: {len(results.bits)}')
        # results = scrape.modbus_client.read_holding_registers(0x0001, slave=addr)
        # print(f'Registers: {results.registers}, Length: {len(results.registers)}')
        # results = scrape.modbus_client.read_holding_registers(0x003, slave=addr)
        # print(f'Registers: {results.registers}, Length: {len(results.registers)}')

        pass