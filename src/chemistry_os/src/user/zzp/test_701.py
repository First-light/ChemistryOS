import time
import sys

sys.path.append('src/chemistry_os/src')
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_addLiquid import Add_Liquid
from facilities.facility_addSolid import Add_Solid
import logging
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_sdk import HN_SDK
from facilities.facility_bath import Bath

# fr5_C = Fr5Arm("fr5C","192.168.60.2")
# time.sleep(3)
# fr5_C.catcher('open')
# exit()

# fr5_C = Fr5Arm("fr5C","192.168.60.2")
# fr5_C.catcher('open')
# exit()
# fr5_C.move_to_desc([330.0,-195.0,380.0,90.0,-45.0,90.0],vel=10)
# input('catch?')
# fr5_C.catcher('close')
# input('ok?')
# fr5_C.move_to_desc([330.0,-195.0,200.0,90.0,-45.0,90.0],vel=10)

# hn_sdk=HN_SDK()
# hn_sdk.add_Solid.turn_on()
# time.sleep(1)
# hn_sdk.add_Solid.tube_hor()
# exit()
def calculate_crc(data):
    # 初始化 CRC 寄存器为 0xFFFF
    crc = 0xFFFF

    # 多项式除数 0x8005
    polynomial = 0x8005

    # 逐字节处理数据
    for byte in data:
        # 将当前字节与 CRC 寄存器的低字节异或
        crc ^= byte

        # 循环左移 8 位，处理每个位
        for _ in range(8):
            # 如果最高位（第 16 位）为 1，则与多项式异或
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1

            # 将 CRC 寄存器限制为 16 位
            crc &= 0xFFFF

    # 返回 CRC 校验值的高字节和低字节
    return (crc & 0xFF), ((crc >> 8) & 0xFF)

# 输入数据
data_str = "110300070001"
# 将字符串转换为字节数据
data_bytes = bytes.fromhex(data_str)

# 计算 CRC 校验值
crcl, crch = calculate_crc(data_bytes)

# 输出结果
print(f"CRCL: {crcl:02X}")
print(f"CRCH: {crch:02X}")
logging.basicConfig(level=logging.DEBUG)
with Add_Solid(mcu_addr=0x10) as controller:
    controller.clip_close(block=False)
    time.sleep(1)


with Add_Solid(initial_mode=Add_Solid.ThreadMode.MCU_MODE) as controller:
    # print(controller.read_frame() == None)
    controller.turn_on()
    # print(controller.read_frame() == None)
    controller.clip_open()

    controller.clip_close()

    # controller.tube_hor()
    # # logging.debug(controller.read_frame())
    # # controller.add_solid_series(0.5)
    # # logging.debug('fine')
    # # monitor_and_plot_weight(controller)
    # # controller.wait_until_idle()
    # # time.sleep(0)
    # print(controller.read_frame())
    # controller.tube_ver()
    # # controller.clip_open()

    controller.turn_off()
    # time.sleep(1)
    # controller.turn_on(block=False)
    # time.sleep(1)
    # print(controller.read_frame())
exit(0)


add_Liquid=Add_Liquid('add_Liquid')
add_Solid=Add_Solid('add_Solid')
fr5_C = Fr3Arm("fr3C","192.168.58.3")
fr5_A = Fr5Arm("fr5A","192.168.58.2")
bath = Bath('bath')
fr5_C.move_to_catch()
# fr5_A.set_nowplace(3)

# hn_sdk=HN_SDK()
# add_Solid.turn_on()
# time.sleep(1)
# add_Solid.clip_close()
# time.sleep(1)
# add_Solid.clip_open()
# time.sleep(1)
# add_Solid.turn_off()
# exit()
# add_Liquid=Add_Liquid('add_Liquid')
# add_Solid=Add_Solid('add_Solid')
hn_sdk=HN_SDK()
hn_sdk.fr5_init()
# hn_sdk.name_catch('beaker')
# hn_sdk.name_put('add_solid_place')

# hn_sdk.name_catch('test_tube')
# hn_sdk.name_put('test_tube')

hn_sdk.name_catch('sanjinshaoping')
hn_sdk.bath_put('bath_fr5')
hn_sdk.bath_catch('bath_fr5')
hn_sdk.name_put('sanjinshaoping')



