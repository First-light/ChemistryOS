# coding=utf-8
import enum
import logging
import struct
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List

import serial

from facility import Facility

# --- 配置常量 ---
# 可以移到 AddSolid 的 __init__ 或作为类变量，这里为方便演示先放外面
DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'
DEFAULT_BAUD_RATE = 9600
DEFAULT_SEND_INTERVAL_MS = 100  # MCU发送状态的典型间隔

class Add_Solid(Facility):
    # --- 枚举定义 ---
    class ExitCode(enum.IntEnum):
        OK = 0
        ERROR = -1
        OUT_OF_RANGE = -2
        TIMEOUT = -3

    class McuCommandCode(enum.Enum):
        IDLE = 0x41         # 空指令/响应
        CLIP_OPEN = 0x42    # 夹爪打开
        CLIP_CLOSE = 0x43   # 夹爪关闭
        TUBE_HOR = 0x44     # 试管抬起
        TUBE_VER = 0x45     # 试管放平
        DAC = 0x46          # 设置DAC值
        PID = 0x47          # 设置PID参数
        BEGIN = 0x48        # 开始称量
        TURN_ON = 0x49      # 启用 MCU 输出，上位机切换 MCU_MODE
        TURN_OFF = 0x4A     # 禁用 MCU 输出，上位机切换 HOST_MODE，称量中禁止发送

    class McuStatus(enum.Enum):
        IDLE = 0
        BUSY = 0x01010101

    """
    主控制类，用于与固液添加模块的MCU通过自有协议进行通信。
    管理串口通信线程，提供阻塞式API。
    """
    # 将枚举和常量作为类属性，方便访问
    type = "Add_Solid"
    CommandCode = McuCommandCode
    Status = McuStatus
    Exit = ExitCode

    # --- 内部数据结构 ---
    @dataclass
    class McuStatusCommandTypedef:
        """解析并保存MCU状态数据"""
        addr: int = 0
        # cmd: int = 0  # 应该总是 0x41 (IDLE)
        weight_target: float = 0.0
        weight_now: float = 0.0
        p: float = 0.0
        d: float = 0.0
        offset: float = 0.0
        status_raw: int = 0  # 原始状态值
        status: 'Add_Solid.Status' = field(init=False)      # 解析后的枚举状态
        time_ns: int = 0
        raw_frame: bytes = field(default=b'', repr=False)

        def __post_init__(self):
            # 在初始化后根据 status_raw 设置枚举状态
            self.time_ns = time.time_ns()
            try:
                self.status = Add_Solid.Status(self.status_raw)
            except ValueError:
                logging.warning(f"收到未知的原始状态值: {self.status_raw:#x}")
                self.status = Add_Solid.Status.IDLE

        @classmethod
        def parse(cls, frame: bytes) -> Optional['Add_Solid.McuStatusCommandTypedef']:
            """
            从字节串解析MCU状态帧 (小端序)。
            协议帧: Addr(1) Cmd(1) WeightTarget(4) WeightNow(4) P(4) D(4) Offset(4) Status(4)
            总长度应为 26字节。 Cmd 必须是 0x41。
            """
            expected_length = 26
            if not frame or len(frame) != expected_length:
                logging.error(f"状态帧解析错误：期望长度 {expected_length}，实际长度 {len(frame)}")
                return None
            if frame[1] != Add_Solid.CommandCode.IDLE.value:
                logging.error(f"状态帧解析错误：期望命令 {Add_Solid.CommandCode.IDLE.value:#04x}，实际为 {frame[1]:#04x}")
                return None

            try:
                # '<': 小端序, B: uchar(1), f: float(4), I: uint(4)
                unpacked_data = struct.unpack('< B B f f f f f I', frame)
                return cls(
                    addr=unpacked_data[0],
                    # cmd=unpacked_data[1],
                    weight_target=unpacked_data[2],
                    weight_now=unpacked_data[3],
                    p=unpacked_data[4],
                    d=unpacked_data[5],
                    offset=unpacked_data[6],
                    status_raw=unpacked_data[7],  # 先存原始值
                    raw_frame=frame
                )
            except struct.error as e:
                logging.error(f"状态帧结构体解包错误: {e}，帧数据 (前8字节): {frame[:8].hex()}")
                return None
            except Exception as e:
                logging.error(f"状态帧解析时发生未知错误: {e}")
                return None

    @dataclass
    class McuControlCommandTypedef:
        """构建发送给MCU的控制命令帧"""
        addr: int
        cmd: 'Add_Solid.CommandCode'
        data: List[float] = field(default_factory=list)  # 使用float列表存储数据
        waiting_time: Optional[float] = None
        trigger: Optional[threading.Event] = None

        def build_frame(self) -> bytes:
            """构建命令帧字节串 (小端序)"""
            frame = bytearray()
            frame.append(self.addr)
            frame.append(self.cmd.value)

            if self.data:
                for val in self.data:
                    frame.extend(struct.pack('<f', val))
            else:
                # 如果没有数据，确保至少有4字节填充 (根据协议，0x00000000)
                frame.extend(struct.pack('<I', 0))  # 发送一个4字节的0

            # 注意：这里没有包含CRC或校验和
            return bytes(frame)

    class ThreadMode(enum.Enum):
        HOST_MODE = 0,
        MCU_MODE = 1

    def __init__(self,
                 name: str = 'add_Solid',
                 comm: str = DEFAULT_SERIAL_PORT,
                 baud_rate: int = DEFAULT_BAUD_RATE,
                 send_interval_ms: int = DEFAULT_SEND_INTERVAL_MS,
                 addr: int = 0x01,
                 initial_mode: Optional['Add_Solid.ThreadMode'] = None):
        super().__init__(name, Add_Solid.type)

        # 串口设置
        self.ser = None  # 串口设备
        self.comm = comm
        self.baud_rate = baud_rate
        self.send_interval_ms = send_interval_ms

        # 通信设置 8N1
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE

        # 通信识别
        self.addr = addr

        # 时序设置
        _, self._t3_5, self._initial_wait_sec = self._calculate_timing()

        self._thread: Optional['Add_Solid.SerialHandlerThread'] = None
        self._mode = None
        self._change_mode(initial_mode)

        # FIFO 队列，保存最近10帧状态
        self.fifo_frame: deque['Add_Solid.McuStatusCommandTypedef'] = deque(maxlen=10)

    def _calculate_timing(self):
        bits_per_char = 1 + self.bytesize + (0 if self.parity == serial.PARITY_NONE else 1) + self.stopbits
        char_time_sec = bits_per_char / self.baud_rate
        t1_5 = 1.5 * char_time_sec
        t3_5 = 3.5 * char_time_sec
        if self.baud_rate > 19200:
            t1_5 = max(t1_5, 0.00075)
            t3_5 = max(t3_5, 0.00175)
        return t1_5, t3_5, self.send_interval_ms / 1000.0 * 1.5

    def initialize_serial(self) -> bool:
        if self.ser and self.ser.is_open:
            # logging.info(f"串口 {self.comm} 已经打开.")
            return True

        try:
            self.ser = serial.Serial(
                port=self.comm, baudrate=self.baud_rate,
                bytesize=self.bytesize, parity=self.parity, stopbits=self.stopbits,
                timeout=self._t3_5 * 2  # 初始短超时用于清空
            )
            logging.info(f"串口 {self.comm} 打开成功.")
            # 清空缓冲区
            # time.sleep(0.1)  # 等待串口稳定
            if self.ser.in_waiting > 0:
                discarded = self.ser.read(self.ser.in_waiting)
                logging.debug(f"初始化丢弃 {len(discarded)} 字节: {discarded.hex()}")
            # self._last_comm_time = time.monotonic()  # 初始化通信时间
            return True
        except serial.SerialException as e:
            logging.error(f"无法打开或配置串口 {self.comm}: {e}")
            self.ser = None
            return False
        # except Exception as e:
        #     logging.error(f"初始化串口时发生未知错误: {e}")
        #     self.ser = None
        #     # return False
        #     raise e

    def _read_raw_frame(self) -> Optional[bytes]:
        """读取一帧，考虑时序，返回原始字节串"""
        if not self.ser or not self.ser.is_open: return None

        frame_buffer = bytearray()

        try:
            self.ser.timeout = self._initial_wait_sec

            first_byte = self.ser.read(1)
            if not first_byte: return None  # 超时未收到

            frame_buffer.extend(first_byte)
            # self._last_comm_time = time.monotonic()  # 更新通信时间
            self.ser.timeout = self._t3_5  # 后续字节用 T3.5

            while True:
                byte = self.ser.read(1)
                if byte:
                    # self._last_comm_time = time.monotonic()  # 更新通信时间
                    frame_buffer.extend(byte)
                else:  # 超时
                    # logging.debug((time.monotonic() - self._last_comm_time) / self._t3_5)
                    break
        except serial.SerialException as e:
            logging.error(f"读取串口时发生错误: {e}")
            return None
        except Exception as e:
            logging.error(f"读取帧时发生未知错误: {e}")
            return None

        if not frame_buffer:
            return None
        else:
            logging.debug(f"成功读取一帧，长度: {len(frame_buffer)}")
            return bytes(frame_buffer)

    def _drop_frame(self, frame: bytes) -> bool:
        """判断是否为我们关心的MCU状态帧 (Cmd 0x41, len 26)"""
        if (frame and len(frame) == 26
                and frame[0] == self.addr and frame[1] == Add_Solid.CommandCode.IDLE.value):
            # 这是我们期望的 MCU 状态帧，不丢弃
            return False
        else:
            # 其他帧，可能是 Modbus RTU 通信或其他噪声，丢弃
            prefix = bytes(frame[:8]).hex() if frame else "N/A"
            length = len(frame) if frame else 0
            logging.debug(f"丢弃帧: 长度={length}, 前8字节={prefix}" if frame else "丢弃空帧")
            return True

    def _read_needed_frame(self, timeout: Optional[float]=None) -> Optional[bytes]:
        """读取一帧，直到超时或读取到我们关心的帧"""
        # 确保串口已打开
        if not timeout:
            timeout = self._initial_wait_sec

        start_time = time.thread_time_ns()
        end_time = start_time

        frame = self._read_raw_frame()
        # 当帧未超时且不是我们关心的帧时，继续读取
        while frame and self._drop_frame(frame) and (end_time - start_time) / 1.0e9 < timeout:
            frame = self._read_raw_frame()
            end_time = time.thread_time_ns()

        if frame and not self._drop_frame(frame):
            return frame
        return None

    def _send_frame(self, frame_to_send: bytes):
        """发送帧，确保 T3.5 间隔"""
        if not self.ser or not self.ser.is_open:
            logging.error("发送失败：串口未打开")
            return False

        try:
            # 确保距离上次通信（读或写）至少 T3.5
            # current_time = time.monotonic()
            # time_since_last = (current_time - self._last_comm_time) / 1000.0
            # wait_time = self._t3_5 - time_since_last
            # if wait_time > 0 and False:
            #     logging.debug(f"等待 T3.5 间隔: {wait_time:.4f}s")
            #     time.sleep(wait_time)

            # logging.debug(f"发送帧: {frame_to_send.hex()}")
            self.ser.write(frame_to_send)
            self.ser.flush()
            # self._last_comm_time = time.monotonic()  # 更新最后通信时间
            return True
        except serial.SerialException as e:
            logging.error(f"发送串口数据时发生错误: {e}")
            return False
        except Exception as e:
            logging.error(f"发送帧时发生未知错误: {e}")
            return False

    def _change_mode(self, mode: Optional['Add_Solid.ThreadMode']):
        """切换模式"""
        # 仅能由主线程调用
        previous_mode = self._mode
        if mode is None:
            # 尝试读取当前模式
            if self._read_needed_frame(timeout=self._initial_wait_sec * 2):
                self._mode = Add_Solid.ThreadMode.MCU_MODE
            else:
                self._mode = Add_Solid.ThreadMode.HOST_MODE
        else:
            # 设置模式
            self._mode = mode

        if previous_mode == self._mode:
            logging.debug(f"模式未改变: {self._mode}")
            return
        else:
            logging.info(f"模式已改变: {previous_mode} -> {self._mode}")
            if self._mode == Add_Solid.ThreadMode.MCU_MODE:
                self._thread = self.SerialHandlerThread(self)
                self._thread.start()
            elif self._mode == Add_Solid.ThreadMode.HOST_MODE:
                if self._thread and self._thread.is_alive():
                    self._thread.stop()
                    self._thread.join()
                self._thread = None

    def send_command(self, cmd: 'Add_Solid.McuControlCommandTypedef') -> bool:
        status = False
        # if self.initialize_serial():
        if self.ser and self.ser.is_open:
            if self._mode == Add_Solid.ThreadMode.HOST_MODE:
                self._send_frame(cmd.build_frame())
                status = True
            elif self._mode == Add_Solid.ThreadMode.MCU_MODE:
                if self._thread and self._thread.is_alive():
                    status = self._thread.send_command(cmd, timeout=self._initial_wait_sec * 2.5)

        if status:
            self.log.info(f"发送命令: {cmd.cmd.name}，数据: {cmd.data}")
            if cmd.cmd == Add_Solid.CommandCode.TURN_ON:
                self._change_mode(Add_Solid.ThreadMode.MCU_MODE)
            if cmd.cmd == Add_Solid.CommandCode.TURN_OFF:
                self._change_mode(Add_Solid.ThreadMode.HOST_MODE)

            if cmd.waiting_time:
                time.sleep(cmd.waiting_time)

            if self._mode == Add_Solid.ThreadMode.MCU_MODE:
                print('等待直到 MCU 状态空闲')
                status = self._thread.wait_until_idle()

        return status

    # --- 内部串口处理线程 ---
    class SerialHandlerThread(threading.Thread):
        def __init__(self, upper: 'Add_Solid',
                     ):
            super().__init__(name="SerialHandlerThread", daemon=True)  # 设置为守护线程
            self.upper = upper

            self.ser = self.upper.ser

            self._frame_arrive_event = threading.Event()
            self._stop_status = False
            self.latest_frame: 'Add_Solid.McuStatusCommandTypedef' = Add_Solid.McuStatusCommandTypedef(
                                addr=self.upper.addr
                            )

            self.sending_cmd = None
            self.sending_event = threading.Event()
            self.sending_lock = threading.Lock()

        def send_command(self, cmd: 'Add_Solid.McuControlCommandTypedef', timeout: Optional[float]=None) -> bool:
            """发送命令到 MCU"""
            # 仅在主线程中调用
            if self._stop_status:
                logging.error("线程已停止，无法发送命令")
                return False

            with self.sending_lock:
                if self._stop_status:
                    logging.error("线程已停止，无法发送命令")
                    return False

                self.sending_cmd = cmd
                self.sending_event.clear()
                status = self.sending_event.wait(timeout=timeout)
                self.sending_event.clear()
                self.sending_cmd = None
                return status

        def run(self):
            assert self.ser and self.ser.is_open

            timeout_count = 0
            while not self._stop_status and self.upper._mode == Add_Solid.ThreadMode.MCU_MODE:
                received_frame = self.upper._read_needed_frame()
                if received_frame:
                    self.latest_frame = Add_Solid.McuStatusCommandTypedef.parse(received_frame)
                    self.upper.fifo_frame.append(self.latest_frame)
                    self._frame_arrive_event.set()

                    if timeout_count > 0:
                        timeout_count = 0
                    elif timeout_count < 0:
                        timeout_count += 1
                else:
                    timeout_count += 1
                    if timeout_count >= 20:
                        self.upper.log.error("串口离线或者 MCU 状态错误，切换 HOST 模式")
                        self.upper._mode = Add_Solid.ThreadMode.HOST_MODE
                        self._stop_status = True
                        break
                    continue

                # 发送命令
                sending_cmd = self.sending_cmd
                if not sending_cmd:
                    sending_cmd = Add_Solid.McuControlCommandTypedef(
                        addr=self.upper.addr,
                        cmd=Add_Solid.CommandCode.IDLE
                    )
                self.upper._send_frame(sending_cmd.build_frame())
                if sending_cmd == self.sending_cmd:
                    self.sending_event.set()
                    self.sending_cmd = None

                # since python 3.10
                match sending_cmd.cmd:
                    case Add_Solid.CommandCode.TURN_ON:
                        self.upper.log.info("切换 MCU 模式")
                        self.upper._mode = Add_Solid.ThreadMode.MCU_MODE
                    case Add_Solid.CommandCode.TURN_OFF:
                        self.upper.log.info("切换 HOST 模式")
                        self.upper._mode = Add_Solid.ThreadMode.HOST_MODE
                    case Add_Solid.CommandCode.BEGIN:
                        # TODO, in a hacky way
                        timeout_count -= int(7.0 / self.upper._initial_wait_sec) + 1
                    case _:
                        pass

                if not received_frame or not sending_cmd:
                    time.sleep(0.001)

            self._stop_status = True
            self._frame_arrive_event.set()
            self.sending_event.set()

        def stop(self):
            with self.sending_lock:
                self._stop_status = True

        def wait_until_idle(self, timeout: Optional[float] = None) -> bool:
            start_time = time.thread_time_ns()
            end_time = time.thread_time_ns()
            period = (start_time - end_time) / 1.0e9
            while not timeout or period < timeout:
                if self._frame_arrive_event.wait(timeout=timeout - period if timeout else 1.0):
                    self._frame_arrive_event.clear()
                end_time = time.thread_time_ns()
                period = (start_time - end_time) / 1.0e9
                if self.is_alive() and not self._stop_status:
                    if self.latest_frame.status == Add_Solid.Status.IDLE and self.sending_cmd is None:
                        return True
                else:
                    return True
            return False

    def cmd_init(self):
        """注册命令到解析器"""
        self.parser.register("add_solid_turn_on", self.turn_on, None, "Turn on the add solid device")
        self.parser.register("add_solid_turn_off", self.turn_off, None, "Turn off the add solid device")
        self.parser.register("add_solid_clip_open", self.clip_open, None, "Open the clip of add solid device")
        self.parser.register("add_solid_clip_close", self.clip_close, None, "Close the clip of add solid device")
        self.parser.register("add_solid_tube_hor", self.tube_hor, None, "Set tube to horizontal position")
        self.parser.register("add_solid_tube_ver", self.tube_ver, None, "Set tube to vertical position")
        self.parser.register("add_solid_set_dac", self.set_dac, {"dac":0.0}, "Set DAC value of add solid device")
        self.parser.register("add_solid_set_pid", self.set_pid, {"kp":0.0, "kd":0.0, "offset":0.0}, "Set PID parameters of add solid device")
        self.parser.register("add_solid_add_series", self.add_solid_series, {"weight":0.0}, "Add solid series operation")

    def __del__(self):
        # 确保在对象销毁时停止线程
        self.stop()

    def stop(self):
        self._thread.stop()

    def turn_on(self) -> bool:
        """打开设备。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.TURN_ON
        ))

    def turn_off(self) -> bool:
        """关闭设备。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.TURN_OFF
        ))

    def clip_open(self) -> bool:
        """打开夹爪。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.CLIP_OPEN,
                waiting_time=2
        ))

    def clip_close(self) -> bool:
        """关闭夹爪。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.CLIP_CLOSE,
                waiting_time=2
        ))

    def tube_hor(self) -> bool:
        """将管子设置为水平位置。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.TUBE_HOR,
                waiting_time=5.5
        ))

    def tube_ver(self) -> bool:
        """将管子设置为垂直位置。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.TUBE_VER,
                waiting_time=5.5
        ))

    def set_dac(self, dac: float) -> bool:
        """设置 DAC 值。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.DAC,
                data=[dac]
        ))

    def set_pid(self, kp: float, kd: float, offset: float) -> bool:
        """设置 PID 参数。"""
        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.PID,
                data=[kp, kd, offset]
        ))

    def add_solid_series(self, weight: float) -> bool:
        """开始添加指定重量的固体系列操作。"""
        if self._mode == Add_Solid.ThreadMode.HOST_MODE:
            raise Exception("当前模式为 HOST_MODE，无法执行添加固体系列操作。")
            if not self.turn_on():
                return False

        return self.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.addr,
                cmd=Add_Solid.CommandCode.BEGIN,
                data=[weight],
                waiting_time=7
        ))

    def read_frame(self, timeout: Optional[float] = None) -> Optional['Add_Solid.McuStatusCommandTypedef']:
        if self._thread.is_alive() and not self._thread._stop_status and self._mode == Add_Solid.ThreadMode.MCU_MODE:
            if not timeout:
                timeout = self._initial_wait_sec * 2.5
            if self._thread._frame_arrive_event.wait(timeout=timeout):
                return self._thread.latest_frame

        return None

    def read_frame_fifo(self) -> Optional['Add_Solid.McuStatusCommandTypedef']:
        """读取 FIFO 队列中的最新帧"""
        if len(self.fifo_frame) > 0:
            return self.fifo_frame.popleft()
        return None

    def release_serial(self) -> bool:
        """释放串口资源"""
        if not (self.ser and self.ser.is_open):
            return True
        if self._mode == Add_Solid.ThreadMode.MCU_MODE and self._thread and self._thread.is_alive():
            self._thread.stop()
            self._thread.join()
        try:
            self.ser.close()
            logging.info(f"串口 {self.comm} 关闭成功.")
            return True
        except serial.SerialException as e:
            logging.error(f"关闭串口 {self.comm} 时发生错误: {e}")
            return False

# 测试读取功能正常：20250425
# len = 8 读天平
# len = 13 天平回数据
# len = 26 截获
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    controller = Add_Solid(comm='/dev/ttyUSB0', baud_rate=9600, addr=0x01)
    controller.initialize_serial()
    # frame = controller._thread._read_frame()
    # logging.debug(frame)
    #
    # while frame:
    #     frame = controller._thread._read_frame()
    #     if not controller._thread._drop_frame(frame):
    #         break
    # send_cmd = AddSolid.McuControlCommandTypedef(addr=0x01, cmd=AddSolid.CommandCode.TURN_ON)
    # logging.debug(controller._thread._send_frame(send_cmd.build_frame()))
    # time.sleep(0.4)
    #
    # while True:
    #     frame = controller._thread._read_frame()
    #     if not controller._thread._drop_frame(frame):
    #         logging.debug(frame[2:].hex(sep=' ', bytes_per_sep=4))
    #         logging.debug('解析数据')
    #         status = AddSolid.McuStatusCommandTypedef.parse(frame)
    #         logging.debug(status)
    #         break
    #
    # send_cmd = AddSolid.McuControlCommandTypedef(addr=0x01, cmd=AddSolid.CommandCode.TURN_OFF)
    # logging.debug(controller._thread._send_frame(send_cmd.build_frame()))
    # logging.debug(controller._thread._read_frame()) # 超时
    print(controller.read_frame() is None)
    controller.turn_on()
    # controller.clip_open()

    # controller.clip_close()
    controller.tube_hor()
    # logging.debug(controller.read_frame())
    # controller.add_solid_series(0.5)
    # logging.debug('fine')
    # monitor_and_plot_weight(controller)
    # controller.wait_until_idle()
    # time.sleep(0)
    print(controller.read_frame())
    controller.tube_ver()
    # controller.clip_open()

    controller.turn_off()