"""
描述:
    本文件定义了 HN_SDK 类，这是 Chemistry OS 的软件开发工具包 (SDK) 的核心模块。
    该模块封装了多个设备的操作逻辑，包括机械臂、加液装置、加固体装置和水浴锅等。
    提供了高层次的接口，用于实现复杂的化学实验自动化操作。

主要功能:
    - 控制机械臂 (Fr5Arm 和 Fr3Arm) 的抓取、放置、倒液等操作。
    - 操作加液装置和加固体装置，实现液体和固体的精确添加。
    - 控制水浴锅的加热、制冷、搅拌等功能。
    - 提供倒计时功能，用于实验过程中的时间控制。

类:
    HN_SDK:
        - 初始化多个设备实例。
        - 提供高层次的操作接口，如抓取、放置、倒液、加液、加固体等。
        - 封装了设备的具体操作逻辑，简化了用户的调用流程。

依赖:
    - threading: 用于多线程操作。
    - time: 用于时间控制。
    - sys: 用于系统路径管理和输入监听。
    - select: 用于监听键盘输入。
    - Chemistry OS 的设备模块:
        - facilities.facility_fr5arm: 控制 Fr5Arm 机械臂。
        - facilities.facility_fr3arm: 控制 Fr3Arm 机械臂。
        - facilities.facility_addLiquid: 控制加液装置。
        - facilities.facility_addSolid: 控制加固体装置。
        - facilities.facility_bath: 控制水浴锅。

作者:
    朱振鹏

版本:
    1.0.0

日期:
    2025年5月7日
"""
import select
import threading
import time
import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_addLiquid import Add_Liquid
from facilities.facility_addSolid import Add_Solid
from facilities.facility_bath import Bath

class HN_SDK(Facility):
    
    def __init__(self):
        self.name = "Chemistry OS SDK"
        self.version = "1.0.0"
        self.description = "A software development kit for Chemistry OS."
        self.fr5_A = Fr5Arm("fr5A","192.168.58.2")
        self.fr3_C = Fr3Arm("fr3C","192.168.58.3")
        self.add_Liquid=Add_Liquid('add_Liquid')
        self.add_Solid=Add_Solid('add_Solid')
        self.bath=Bath('bath')

    def name_catch(self, name:str):

        obj_statu = self.fr5_A.obj_status[name]
        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        self.fr5_A.catch()
        time.sleep(1)

        #抬起
        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=10)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)
        
    def name_put(self, name:str):
        obj_statu = self.fr5_A.obj_status[name]

        # #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, dest, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=10)

        self.fr5_A.put()

        time.sleep(1)

        #移动出去
        self.fr5_A.move_by(obj_statu['catch_pre_xyz_offset'][0], obj_statu['catch_pre_xyz_offset'][1], obj_statu['catch_pre_xyz_offset'][2], vel=10)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

    def pour(self, name:str):
        obj_statu = self.fr5_A.obj_status[name]

        # #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, dest, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=10)

        self.fr5_A.robot.StartJOG(0,6,-1,130.0,vel=100.0,acc=100.0)
        time.sleep(6)
        self.fr5_A.robot.ImmStopJOG()

        time.sleep(3)

        joint_pos = self.fr5_A.robot.GetActualJointPosDegree(0)[1]
        max_angel = joint_pos[5] + 6.0
        min_angel = joint_pos[5] - 6.0
        t=0.003
        shakes = 0
        i=-2
        while shakes < 600:
            self.fr5_A.robot.ServoJ(joint_pos, 0.0, 0.0, t, 0.0, 0.0)
            if joint_pos[5] > max_angel:
                i = -1
            if joint_pos[5] < min_angel:
                i = 1
            joint_pos[5] += i

            time.sleep(t)
            shakes += 1
        
        time.sleep(2)

        self.fr5_A.robot.StartJOG(0,6,1,130.0,vel=100.0,acc=100.0)
        time.sleep(6)

        self.fr5_A.robot.ImmStopJOG()

        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=10)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

    def bath_catch(self, name:str):

        obj_statu = self.fr5_A.obj_status[name]

        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=10)
        time.sleep(1)

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        
        self.fr5_A.robot.MoveGripper(1, 15, 50, 10, 10000, 1)
        time.sleep(3)
        self.fr3_C.put()
        time.sleep(1)
        self.fr5_A.catch()
        time.sleep(1)

        #移动到准备位置
        desc_pos_aim_xyz = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['bath_pre_offset']))
        desc_pos_aim_pre_2 = desc_pos_aim_xyz + obj_statu['catch_direction']
        desc_pos_aim_pre_1 = list(map(lambda x, y: x + y, desc_pos_aim_xyz, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre_2, vel=10)
        time.sleep(1)
        self.fr5_A.move_to_desc(desc_pos_aim_pre_1, vel=10)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

    def bath_put(self, name:str):

        obj_statu = self.fr5_A.obj_status[name]

        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim_xyz = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['bath_pre_offset']))
        desc_pos_aim_pre_2 = desc_pos_aim_xyz + obj_statu['catch_direction']
        desc_pos_aim_pre_1 = list(map(lambda x, y: x + y, desc_pos_aim_xyz, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre_1, vel=10)
        time.sleep(1)
        self.fr5_A.move_to_desc(desc_pos_aim_pre_2, vel=10)
        time.sleep(1)

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        self.fr5_A.robot.MoveGripper(1, 15, 50, 10, 10000, 1)
        time.sleep(1)
        self.fr3_C.catch()
        time.sleep(1)
        self.fr5_A.put()
        time.sleep(1)

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=10)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

    def add_liquid(self, name:str, rpm=150, volume=0.0, name_space='add_liquid_mode_place'):

        obj_statu = self.fr5_A.obj_status[name]

        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        self.fr5_A.robot.MoveGripper(1, 50, 50, 100, 10000, 0)

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        self.fr5_A.catch()
        time.sleep(1)

        #抬起
        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=10)
        time.sleep(1)

        obj_statu = self.fr5_A.obj_status[name_space]
        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=10)
        time.sleep(1)

        self.add_Liquid.add_liquid(name, rpm, volume)
        time.sleep(1)

        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=10)

        obj_statu = self.fr5_A.obj_status[name]
        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=10)
        self.fr5_A.robot.MoveGripper(1, 50, 50, 100, 10000, 0)
        time.sleep(1)

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=10)
        time.sleep(1)
        self.fr5_A.put()

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

    def add_solid(self, name:str, gram:float, name_space='add_solid_place'):
        self.name_catch_and_put(name, name_space)
        self.add_Solid.turn_on()
        self.add_Solid.tube_hor()
        self.add_Solid.add_solid_series(gram)
        self.add_Solid.tube_ver()
        self.add_Solid.turn_off()
        self.pour()

    def fr3_move_to_catch(self):
        self.fr3_C.move_to_catch()

    def fr3_move_to_bath_fr5(self):
        self.fr3_C.move_to_bath_fr5()

    def fr3_catch(self):
        self.fr3_C.catch()

    def fr3_put(self):
        self.fr3_C.put()
    
    def name_catch_and_put(self, name1:str, name2:str):
        self.name_catch(name1)
        self.name_put(name2)

    def name_pour(self, name1:str, name2:str, name3:str):
        self.name_catch(name1)
        self.pour(name2)
        self.name_put(name3)

    def fr5_gripper_activate(self):
        self.fr5_A.gripper_activate()

    def fr5_Go_to_start_zone_0(self):
        self.fr5_A.Go_to_start_zone_0()

    def bath_init(self):
        self.bath.mix_ctr(1)
        self.bath.circle_ctr(1)# 允许circle
        self.bath.hot_ctr(1)# 加热
        self.bath.cold_ctr(1)# 允许制冷

    def bath_close(self):
        self.bath.mix_ctr(0)
        self.bath.circle_ctr(0)# 禁止circle
        self.bath.hot_ctr(0)# 禁止加热
        self.bath.cold_ctr(0)# 禁止制冷

    def bath_writetmp(self, tmp:float):
        Bath.interactable_writetmp(tmp)

    def interactable_countdown(seconds):
    # 用于控制是否继续计时的事件
        stop_event = threading.Event()
        countdown_finished_event = threading.Event()

        def countdown(seconds):
            start_time = time.time()  # 获取当前时间
            end_time = start_time + seconds  # 计算结束时间

            while seconds > 0 and not stop_event.is_set():  # 计时中如果stop_event触发就停止
                # 计算剩余时间
                now = time.time()
                remaining_time = end_time - now
                # 计算预计完成时间
                finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
                # 打印剩余时间和预计完成时间
                print(f"剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}, 输入 \'q\' 以跳过", end="\r")
                time.sleep(1)
                seconds -= 1

            if not stop_event.is_set():
                print("\n时间到")
                countdown_finished_event.set()

        def check_exit():
            # 监听键盘输入，按 'q' 停止倒计时
            while not countdown_finished_event.is_set():
                if sys.stdin in select.select([sys.stdin], [], [], 1)[0]:  # 使用 select 监听输入
                    input_char = sys.stdin.read(1).strip()  # 读取输入字符
                    if input_char.lower() == 'q':
                        print("\n手动停止计时")
                        stop_event.set()  # 触发事件停止倒计时
                        break  # 停止监听输入，后续程序继续执行
            # print("计时结束，手动停止线程已退出")

        # 创建线程监听键盘输入
        exit_thread = threading.Thread(target=check_exit)
        exit_thread.daemon = True  # 设置为守护线程，使主线程结束时它自动退出
        exit_thread.start()

        # 启动倒计时
        countdown(seconds)

    def HN_init(self):
        self.fr5_gripper_activate()
        self.fr5_Go_to_start_zone_0()
        self.fr3_move_to_catch()
        self.fr3_put()

    