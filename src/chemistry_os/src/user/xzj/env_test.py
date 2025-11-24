# import lib.fairino.Robot as Robot
#
# robot = Robot.RPC('192.168.58.2')
# robot.MoveCart((350, 60, 300, 90, 0, 90), 0, 0)
# robot.MoveGripper()

from pymodbus.client import ModbusSerialClient
import sys


def find_modbus_address():
    # 1. 配置串口连接
    # 注意：timeout设置得非常短(0.1s)，以便快速跳过错误的地址
    client = ModbusSerialClient(
        port='/dev/ttyUSB0',
        baudrate=9600,
        parity='N',  # 根据实际情况修改: 'N'(无), 'E'(偶), 'O'(奇)
        stopbits=1,
        bytesize=8,
        timeout=0.1  # 关键参数：设置短超时以加快扫描速度
    )

    if not client.connect():
        print("无法打开串口")
        return None

    print("开始扫描 Modbus 地址 (1-247)...")

    # 2. 循环扫描所有标准 Modbus 地址
    target_address = None

    # Modbus 从站地址范围通常是 1 到 247
    for addr in range(1, 248):
        try:
            # 尝试读取保持寄存器 0x0002
            # 这里的 slave=addr 就是我们在尝试猜测的地址
            result = client.read_holding_registers(address=0x0002, count=1, slave=addr)

            # 3. 检查是否有响应
            if not result.isError():
                # 如果没有报错，说明设备响应该地址了
                print(f"\n>>> 成功找到设备！地址 (Slave ID) 为: {addr}")

                # 获取寄存器中的值
                reg_value = result.registers[0]
                print(f">>> 寄存器 0x0002 的值为: {reg_value}")

                # 逻辑验证：通常寄存器里存的就是当前地址，对比一下
                if reg_value == addr:
                    print(">>> (验证通过：寄存器值与通讯地址一致)")
                else:
                    print(f">>> (注意：通讯地址是 {addr}，但寄存器内存的值是 {reg_value})")

                target_address = addr
                break  # 找到后立即停止扫描

            else:
                # 这是一个用于显示进度的可选打印，每扫描10个地址打印一次
                if addr % 10 == 0:
                    sys.stdout.write(f"{addr}...")
                    sys.stdout.flush()

        except Exception as e:
            print(f"扫描地址 {addr} 时发生异常: {e}")
            continue

    client.close()

    if target_address is None:
        print("\n扫描完成，未找到任何响应的设备。")
        return None

    return target_address


# 执行函数
if __name__ == "__main__":
    found_addr = find_modbus_address()