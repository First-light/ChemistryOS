# coding=utf-8
from graphlib import TopologicalSorter
from unicodedata import lookup
from webbrowser import Opera

import serial
import threading
import time
import struct
from dataclasses import dataclass, field
import logging
import enum
from queue import Queue, Empty, Full, ShutDown
from typing import Tuple, Optional, List, Union  # 引入类型提示

# --- 配置常量 ---
# 可以移到 AddSolid 的 __init__ 或作为类变量，这里为方便演示先放外面
DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'
DEFAULT_BAUD_RATE = 9600
DEFAULT_SEND_INTERVAL_MS = 100  # MCU发送状态的典型间隔

class Add_Solid:
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
            从字节串解析MCU状态帧 (大端序)。
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
        trigger: Optional[threading.Event] = None

        def build_frame(self) -> bytes:
            """构建命令帧字节串 (大端序)"""
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

    # --- 内部串口处理线程 ---
    class SerialHandlerThread(threading.Thread):
        def __init__(self, owner: 'Add_Solid',
                     initial_mode: 'Add_Solid.ThreadMode',
                     comm: str,
                     baud_rate: int,
                     send_interval_ms: int,
                     mcu_addr: int,
                     host_addr: int,
                     ):
            super().__init__(name="SerialHandlerThread", daemon=True)  # 设置为守护线程
            self.owner = owner

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
            self.mcu_addr = mcu_addr
            self.host_addr = host_addr

            # 时序设置
            _, self._t3_5, self._initial_wait_sec = self._calculate_timing()
            # self._last_comm_time = 0            self._mode = i            self._mode = initial_modenitial_mode


            # 线程控制
            self._mode = initial_mode  # 控制是否等待数据到达
            self._sending_queue = Queue()
            self._sending_lock = threading.Lock()
            self._frame_arrive_event = threading.Event()
            self._stop_event = threading.Event()
            self.latest_frame: Optional['Add_Solid.McuStatusCommandTypedef'] = None


        def run(self):
            if not (self.ser and self.ser.is_open):
                self._initialize_serial()
            else:
                assert False

            timeout_count = 0
            while not self._stop_event.is_set():
                try:
                    received_frame = None
                    if self._mode == Add_Solid.ThreadMode.MCU_MODE:
                        received_frame = self._read_frame_needed()
                        if received_frame:
                            self.latest_frame = Add_Solid.McuStatusCommandTypedef.parse(received_frame)
                            self._frame_arrive_event.set()
                            if timeout_count > 0:
                                timeout_count = 0
                            elif timeout_count < 0:
                                timeout_count += 1
                        else:
                            timeout_count += 1
                            if timeout_count >= 20:
                                logging.warning('串口离线或者 MCU 状态错误，切换 HOST 模式')
                                timeout_count = 0
                                self._mode = Add_Solid.ThreadMode.HOST_MODE
                            continue

                        # self.latest_frame = received_frame
                    else:
                        if not self.latest_frame:
                            self.latest_frame = Add_Solid.McuStatusCommandTypedef(
                                addr=self.host_addr
                            )

                    if not self._sending_queue.empty():
                        command_to_send = self._sending_queue.get_nowait()
                    else:
                        command_to_send = None if self._mode == Add_Solid.ThreadMode.HOST_MODE \
                            else Add_Solid.McuControlCommandTypedef(addr=self.mcu_addr, cmd=Add_Solid.CommandCode.IDLE)

                    if command_to_send:
                        self._send_frame(command_to_send.build_frame())
                        if command_to_send.trigger:
                            command_to_send.trigger.set()
                        if command_to_send.cmd != Add_Solid.CommandCode.IDLE:
                            self._sending_queue.task_done()

                        if command_to_send.cmd == Add_Solid.CommandCode.TURN_ON:
                            logging.info('切换 MCU 模式')
                            self._mode = Add_Solid.ThreadMode.MCU_MODE
                        elif command_to_send.cmd == Add_Solid.CommandCode.TURN_OFF:
                            logging.info('切换 HOST 模式')
                            self._mode = Add_Solid.ThreadMode.HOST_MODE
                        elif command_to_send.cmd == Add_Solid.CommandCode.BEGIN:
                            # TODO, in a hacky way
                            timeout_count = -70

                    if not received_frame or not command_to_send:
                        time.sleep(0.001)

                except serial.SerialException as e:
                    logging.error(e)
                    raise e

            self._stop_event.clear()

        def _calculate_timing(self):
            bits_per_char = 1 + self.bytesize + (0 if self.parity == serial.PARITY_NONE else 1) + self.stopbits
            char_time_sec = bits_per_char / self.baud_rate
            t1_5 = 1.5 * char_time_sec
            t3_5 = 3.5 * char_time_sec
            if self.baud_rate > 19200:
                t1_5 = max(t1_5, 0.00075)
                t3_5 = max(t3_5, 0.00175)
            return t1_5, t3_5, self.send_interval_ms / 1000.0 * 1.5

        def _initialize_serial(self) -> bool:
            try:
                self.ser = serial.Serial(
                    port=self.comm, baudrate=self.baud_rate,
                    bytesize=self.bytesize, parity=self.parity, stopbits=self.stopbits,
                    timeout=0.01  # 初始短超时用于清空
                )
                logging.info(f"串口 {self.comm} 打开成功.")
                # 清空缓冲区
                time.sleep(0.1)  # 等待串口稳定
                if self.ser.in_waiting > 0:
                    discarded = self.ser.read(self.ser.in_waiting)
                    logging.debug(f"初始化丢弃 {len(discarded)} 字节: {discarded.hex()}")
                # self._last_comm_time = time.monotonic()  # 初始化通信时间
                return True
            except serial.SerialException as e:
                logging.error(f"无法打开或配置串口 {self.comm}: {e}")
                self.ser = None
                return False
            except Exception as e:
                logging.error(f"初始化串口时发生未知错误: {e}")
                self.ser = None
                # return False
                raise e

        def _read_frame(self) -> Optional[bytes]:
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
                # logging.debug(f"成功读取一帧，长度: {len(frame_buffer)}")
                return bytes(frame_buffer)

        def _drop_frame(self, frame: bytes) -> bool:
            """判断是否为我们关心的MCU状态帧 (Cmd 0x41, len 26)"""
            if (frame and len(frame) == 26
                    and frame[0] == self.host_addr and frame[1] == Add_Solid.CommandCode.IDLE.value):
                # 这是我们期望的 MCU 状态帧，不丢弃
                return False
            else:
                # 其他帧，可能是 Modbus RTU 通信或其他噪声，丢弃
                prefix = bytes(frame[:8]).hex() if frame else "N/A"
                length = len(frame) if frame else 0
                # logging.debug(f"丢弃帧: 长度={length}, 前8字节={prefix}" if frame else "丢弃空帧")
                return True

        def _read_frame_needed(self) -> Optional[bytes]:
            frame = self._read_frame()
            while frame:
                if not self._drop_frame(frame):
                    break

                frame = self._read_frame()

            return frame

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
                self.ser.flush()  # 确保数据发出
                # self._last_comm_time = time.monotonic()  # 更新最后通信时间
                return True
            except serial.SerialException as e:
                logging.error(f"发送串口数据时发生错误: {e}")
                return False
            except Exception as e:
                logging.error(f"发送帧时发生未知错误: {e}")
                return False

        def send_command(self, cmd: 'Add_Solid.McuControlCommandTypedef'):
            if self._stop_event.is_set():
                return False

            with self._sending_lock:
                try:
                    self._sending_queue.put(cmd)
                    return True
                except (Full, ShutDown):
                    return False

        def stop(self):
            with self._sending_lock:
                while not self._sending_queue.empty():
                    self._sending_queue.get_nowait()
                    self._sending_queue.task_done()
                self._sending_queue.shutdown()
            self._stop_event.set()


    def __init__(self,
                 comm: str = DEFAULT_SERIAL_PORT,
                 baud_rate: int = DEFAULT_BAUD_RATE,
                 send_interval_ms: int = DEFAULT_SEND_INTERVAL_MS,
                 mcu_addr: int = 0x01,
                 host_addr: int = 0x01,
                 initial_mode: 'Add_Solid.ThreadMode' = ThreadMode.HOST_MODE):
        self._thread = Add_Solid.SerialHandlerThread(self, initial_mode,
                                                    comm, baud_rate, send_interval_ms, mcu_addr, host_addr)
        self.mcu_addr = mcu_addr

    def __del__(self):
        # 确保在对象销毁时停止线程
        self.stop()

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        self._thread.stop()

    def turn_on(self, block: bool = True) -> bool:
        """打开设备。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.TURN_ON
        )):
            if block:
                self.wait_until_idle()
            return True
        return False

    def turn_off(self, block: bool = True) -> bool:
        """关闭设备。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.TURN_OFF
        )):
            if block:
                self.wait_until_idle()
            return True
        return False

    def clip_open(self, block: bool = True) -> bool:
        """打开夹爪。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.CLIP_OPEN
        )):
            if block:
                self.wait_until_idle()
                time.sleep(2)
            return True
        return False

    def clip_close(self, block: bool = True) -> bool:
        """关闭夹爪。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.CLIP_CLOSE
        )):
            if block:
                self.wait_until_idle()
                time.sleep(2)
            return True
        return False

    def tube_hor(self, block: bool = True) -> bool:
        """将管子设置为水平位置。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.TUBE_HOR
        )):
            if block:
                self.wait_until_idle()
                time.sleep(6)
            return True
        return False

    def tube_ver(self, block: bool = True) -> bool:
        """将管子设置为垂直位置。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.TUBE_VER
        )):
            if block:
                self.wait_until_idle()
                time.sleep(6)
            return True
        return False

    def set_dac(self, dac: float, block: bool = True) -> bool:
        """设置 DAC 值。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.DAC,
                data=[dac]
        )):
            if block:
                self.wait_until_idle()
            return True
        return False

    def set_pid(self, kp: float, kd: float, offset: float, block: bool = True) -> bool:
        """设置 PID 参数。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.PID,
                data=[kp, kd, offset]
        )):
            if block:
                self.wait_until_idle()
            return True
        return False

    def add_solid_series(self, weight: float, block: bool = True) -> bool:
        """开始添加指定重量的固体系列操作。"""
        if self._thread.send_command(Add_Solid.McuControlCommandTypedef(
                addr=self.mcu_addr,
                cmd=Add_Solid.CommandCode.BEGIN,
                data=[weight]
        )):
            if block:
                self.wait_until_idle()
                time.sleep(7)
            return True
        return False

    def read_frame(self, timeout: Optional[float] = None) -> Optional['Add_Solid.McuStatusCommandTypedef']:
        if self._thread.is_alive() and not self._thread._stop_event.is_set() and self._thread._mode == Add_Solid.ThreadMode.MCU_MODE:
            if self._thread._frame_arrive_event.wait(timeout=timeout):
                return self._thread.latest_frame
        # logging.debug("Thread alive: %s, Stop event set: %s, Mode: %s",
        #               self._thread.is_alive(),
        #               self._thread._stop_event.is_set(),
        #               self._thread._mode)

        return None

    def wait_until_idle(self, timeout: Optional[float] = None) -> bool:
        start_time = time.thread_time_ns()
        end_time = time.thread_time_ns()
        period = (start_time - end_time) / 1.0e9
        while not timeout or period < timeout:
            frame = self.read_frame(timeout=timeout - period if timeout else None)
            period = (start_time - end_time) / 1.0e9
            self._thread._sending_queue.join()
            if not frame:
                return True
            elif frame.status == Add_Solid.Status.IDLE:
                return True
            time.sleep(0.001)
        return False


def monitor_and_plot_weight(controller, exit_threshold=0.005, consecutive_count=20):
    """
    监控加料过程中的重量变化，并在结束后绘制图形。

    Args:
        controller: 包含 _thread._read_frame() 方法的控制器对象。
        exit_threshold (float): 判断重量接近目标的阈值 (g)。
        consecutive_count (int): 连续多少次重量接近目标后退出。
    """
    import matplotlib as plt
    print("等待 MCU 状态变为 BUSY...")
    time.sleep(1)
    # while True:
    #     try:
    #         frame = controller._thread._read_frame()  # 阻塞读取
    #         if frame.status == AddSolid.Status.BUSY:
    #             print("检测到 BUSY 状态，开始记录数据...")
    #             break
    #         # (可选) 如果IDLE状态下读取非常频繁，可以加个短暂休眠避免CPU空转
    #         # time.sleep(0.01)
    #     except Exception as e:
    #         print(f"读取 Frame 时出错: {e}")
    #         return  # 发生错误则退出
    frame = Add_Solid.McuStatusCommandTypedef.parse(controller._thread._read_frame_needed())

    # --- 初始化数据记录 ---
    timestamps_ms = []
    weights_now_g = []

    # 记录进入 BUSY 状态时的初始数据
    start_time_ns = frame.time_ns
    target_weight_g = frame.weight_target  # 假设在 BUSY 过程中目标重量不变
    initial_weight_now = frame.weight_now

    timestamps_ms.append(0)  # 初始时间点为 0 ms
    weights_now_g.append(initial_weight_now)

    print(f"初始状态: Time=0ms, Weight={initial_weight_now:.3f}g, Target={target_weight_g:.3f}g")

    # --- 记录循环 ---
    consecutive_close_readings = 0
    # 检查初始读数是否满足条件
    if target_weight_g - initial_weight_now < exit_threshold:
        consecutive_close_readings = 1

    while True:
        try:
            frame = controller.read_frame()  # 阻塞读取后续数据

            # --- 检查退出条件 ---
            # 1. 状态变回 IDLE
            if frame.status == Add_Solid.McuStatus.IDLE:
                print("MCU 状态变回 IDLE，停止记录。")
                # 将最后一次IDLE状态前的数据点也记录下来（如果需要）
                # elapsed_time_ms = (frame.time_ns - start_time_ns) / 1e6
                # timestamps_ms.append(elapsed_time_ms)
                # weights_now_g.append(frame.weight_now) # 使用IDLE帧的重量或上一个BUSY帧的重量？取决于需求
                # print(f"记录最后一点: Time={elapsed_time_ms:.1f}ms, Weight={frame.weight_now:.3f}g")
                break  # 退出循环

            # 确保仍在 BUSY 状态下才记录和检查 (理论上应该不会跳变，但做个保护)
            if frame.status == Add_Solid.McuStatus.BUSY:
                # 计算相对时间（毫秒）
                elapsed_time_ms = (frame.time_ns - start_time_ns) / 1e6
                current_weight_now = frame.weight_now

                timestamps_ms.append(elapsed_time_ms)
                weights_now_g.append(current_weight_now)

                print(f"数据点: Time={elapsed_time_ms:.1f}ms, Weight={current_weight_now:.3f}g")

                # (可选) 检查目标重量是否变化
                if frame.weight_target != target_weight_g:
                    print(f"警告: 目标重量在 BUSY 状态下发生变化！"
                          f"旧值={target_weight_g:.3f}g, 新值={frame.weight_target:.3f}g")
                    # 可以选择更新目标重量或保持初始值，这里保持初始值
                    # target_weight_g = frame.weight_target

                # 2. 检查重量是否连续接近目标
                if target_weight_g - current_weight_now < exit_threshold:
                    consecutive_close_readings += 1
                    print(f"重量接近目标 ({target_weight_g - current_weight_now:.4f} < {exit_threshold}). "
                          f"连续次数: {consecutive_close_readings}/{consecutive_count}")
                    if consecutive_close_readings >= consecutive_count:
                        print(f"重量连续 {consecutive_count} 次接近目标，停止记录。")
                        break  # 退出循环
                else:
                    # 如果当前读数不满足条件，重置计数器
                    if consecutive_close_readings > 0:
                        print("重量不再接近目标，重置连续次数计数器。")
                    consecutive_close_readings = 0
            else:
                # 如果状态不是 IDLE 也不是 BUSY，可能需要处理异常情况
                print(f"检测到意外状态: {frame.status}, 停止记录。")
                break

        except Exception as e:
            print(f"读取或处理 Frame 时出错: {e}")
            break  # 发生错误则退出循环

    # --- 数据绘图 ---
    if not timestamps_ms or len(timestamps_ms) < 2:  # 需要至少两个点才能画线
        print("记录的数据不足，无法绘制图形。")
        return

    print(f"记录结束，共 {len(timestamps_ms)} 个数据点。开始绘图...")

    plt.figure(figsize=(12, 6))  # 创建图形窗口，可以调整大小

    # 绘制实时重量曲线
    plt.plot(timestamps_ms, weights_now_g, marker='.', linestyle='-', label='实时重量 (Weight Now)')

    # 绘制目标重量水平线
    plt.axhline(y=target_weight_g, color='r', linestyle='--',
                label=f'目标重量 (Target Weight = {target_weight_g:.3f}g)')

    # 添加标题和标签
    plt.title('加料过程重量变化曲线 (Weight Change During Adding Process)')
    plt.xlabel('时间 (Time / ms)')
    plt.ylabel('重量 (Weight / g)')

    # 添加图例
    plt.legend()

    # 添加网格
    plt.grid(True)

    # 自动调整布局
    plt.tight_layout()

    # 显示图形
    plt.show()

# 测试读取功能正常：20250425
# len = 8 读天平
# len = 13 天平回数据
# len = 26 截获
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    controller = Add_Solid(initial_mode=Add_Solid.ThreadMode.HOST_MODE)

    controller.turn_on()
    # controller.clip_close()
    # controller.tube_hor()
    logging.debug(controller.read_frame())
    controller.add_solid_series(0.5)
    logging.debug('fine')
    monitor_and_plot_weight(controller)
    controller.wait_until_idle()
    # time.sleep(0)
    controller.tube_ver()
    # controller.clip_open()
    controller.turn_off()