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
import copy
import threading
import time
import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_thermometer import Thermometer
from facilities.facility_parser import CommandParser
from facilities.flowdisplay import Flowdisplay
from structs import FacilityState
from facility import Facility
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
from facilities.facility_pumps import PumpGroup
from facilities.facility_bath import Bath
from facilities.facility_filter import Filter
from exceptions import *
from utilities.utility_param import ParamTuple, ParamUtils

class HN_SDK(Facility):
    type = "Chemistry OS SDK"
    name = "sdk"
    version = "1.0.0"
    description = "A software development kit for Chemistry OS."
    compound_c = 0.50
    default_speed = 20.0
    default_put_speed = 10.0
    should_safe = False
    solid_config = None
    liquid_config = {
        'HCl': {
            'temp': 10,
            'rpm': 100,
            'volume': 26.8 * 0.8,
            'wash': False,
        },
        'HCl_wash': {
            'temp': 10,
            'rpm': 100,
            'volume': 26.8 * 0.2,
            'wash': True,
        },
        'KMnO4': {
            'temp': 25,
            'rpm': 15,
            'volume': 53.52,
            'wash': False,
        },
        'H2O2': {
            'temp': 10,
            'rpm': 30,
            'volume': 20.0,
            'wash': False,
        },
        'N2H4': {
            'temp': 25,
            'rpm': 15,
            'volume': 1.14,
            'wash': False,
        },
    }
    
    def __init__(self):
        super().__init__(name="sdk", type = HN_SDK.type)

        try:
            # 引用 Facility.tuple_list 中的对象，并提供默认类型

            self.fr5_A: Fr5Arm = Facility.get_facility_by_name("fr5A", Fr5Arm.type,True,True)
            self.fr5_C: Fr5Arm = Facility.get_facility_by_name("fr5C", Fr5Arm.type,True,True)
            self.add_Liquid: PumpGroup = Facility.get_facility_by_name("add_Liquid", PumpGroup.type,True,True)
            self.add_Solid: Add_Solid = Facility.get_facility_by_name("add_Solid", Add_Solid.type,True,True)
            self.bath: Bath = Facility.get_facility_by_name("bath", Bath.type,True,True)
            if self.add_Liquid and self.bath:
                self.add_Liquid.bath = self.bath
            self.filter: Filter = Facility.get_facility_by_name("filter", Filter.type,True,True)
            self.thermometer: Thermometer = Facility.get_facility_by_name("thermometer", Thermometer.type,True,True)
            self.init_dict = ParamUtils.get_init_params(self)

            # 添加温度计线程控制变量
            self.thermometer_stop_event = threading.Event()
            self.thermometer_thread = None
            self.flask_state = 0
            self.tube_state = 0
            self.temp_state = 0

            self.height_level = 0

        except ValueError as e:
            self.log.info(e)

    def cmd_init(self):
        self.parser.register("name_catch", self.name_catch, {"name":''}, "fr5 catch named place")
        self.parser.register("name_put", self.name_put, {"name":''}, "fr5 put named place")
        self.parser.register("name_pour", self.name_pour, {"name":''}, "fr5 pour named place")
        self.parser.register("bath_catch", self.bath_catch, {"name":''}, "fr5 bath catch")
        self.parser.register("bath_put", self.bath_put, {"name":''}, "fr5 bath put")
        self.parser.register("add_liquid", self.add_liquid, {"name":'', "rpm":150, "volume":0.0}, "add liquid to named place")
        self.parser.register("add_liquid_bath", self.add_liquid_bath, {"liquid_name":''}, "add liquid to named place and bath")
        self.parser.register("add_solid", self.add_solid, {"gram":0.0, "tube_from":'', "beaker_from":''}, "add solid to named place")  # 修正参数名
        self.parser.register("name_catch_and_put", self.name_catch_and_put, {"name1":'', "name2":'', "test_tube_add_catch": False, "test_tube_add_put": False}, "fr5 catch name1 and put name2")
        self.parser.register("fr5_gripper_activate", self.fr5_gripper_activate, {}, "activate fr5 gripper")
        self.parser.register("fr5_Go_to_start_zone_0", self.fr5_Go_to_start_zone_0, {}, "fr5 go to start zone 0")
        self.parser.register("bath_open", self.bath_open, {}, "open bath")
        self.parser.register("bath_start", self.bath_start, {}, "initialize bath")
        self.parser.register("bath_over",self.bath_over,{},"bath over")
        self.parser.register("bath_close", self.bath_close, {}, "close bath")
        self.parser.register("bath_writetmp", self.bath_writetmp, {"tmp":0.0, "close_hot":1}, "write temperature to bath")
        self.parser.register("interactable_countdown", self.interactable_countdown, {"seconds":0.0}, "start interactive countdown")
        self.parser.register("fr5A_init", self.fr5A_init, {}, "initialize fr5A")
        self.parser.register("fr5C_init", self.fr5C_init, {}, "initialize fr5C")
        self.parser.register("HN_init", self.HN_init, {}, "initialize HN")
        self.parser.register("add_solid_init", self.add_solid_init, {}, "initialize add_solid")
        self.parser.register("add_liquid_init", self.add_liquid_init, {}, "initialize add_liquid")
        self.parser.register("add_liquid_config_init", self.add_liquid_config_init, {}, "initialize add_liquid_config")
        self.parser.register("add_liquid_config_change", self.add_liquid_config_change, {}, "change add_liquid_config")
        self.parser.register("add_solid_config_init", self.add_solid_config_init, {}, "initialize add_solid_config")
        self.parser.register("move_shaoping_A2C", self.move_shaoping_support2C, {}, "move_shaoping_A2C")
        self.parser.register("move_shaoping_C2A", self.move_shaoping_C2support, {}, "move_shaoping_C2A")
        self.parser.register("confirm_safety", self.confirm_safety, {"text":'ok?'}, "confirm_safety")
        self.parser.register("bath_wash",self.bath_wash,{},"bath_wash")
        self.parser.register("move_wash",self.move_wash,{"wash_place":'', "index":4},"move_wash")
        self.parser.register("bath_update",self.bath_update,{},"bath_update")
        self.parser.register("temp_on",self.temp_on,{},"temp_on")
        self.parser.register("temp_off",self.temp_off,{},"temp_off")
        self.parser.register("temp_start",self.temp_start,{},"temp_start")
        self.parser.register("temp_over",self.temp_over,{},"temp_over")
        self.parser.register("fr5_C_pour",self.fr5_C_pour,{},"fr5_C_pour")
        self.parser.register("reset_all",self.reset_all_facilities,{},"reset_all_facilities")
        self.parser.register("bath_mix",self.bath_mix,{},"bath_mix")

    def cmd_error_handing(self):
        self.facility_emergency = True
        pass

    def cmd_stop_handing(self):
        self.facility_emergency = True
        pass

    def cmd_reset(self):#从error/stop恢复idle的状态
        self.facility_emergency = False
        pass

    def reset_all_facilities(self):
        self.log.info(f"复位所有设备：{self.flask_state}")
        if self.tube_state == 1:
            self.name_catch_and_put('test_tube_add_place', 'test_tube_support', test_tube_add_catch = True, test_tube_add_put = False)
        if self.temp_state == 1:
            self.temp_off()
        if self.flask_state == 2:
            self.name_put('sanjinshaoping_support_put')
        elif self.flask_state == 1:
            self.move_shaoping_C2support()

        self.bath_over()
        self.HN_init()
        self.fr5_A.move_to_safe_catch(0)
        self.fr5_C.move_to_safe_catch(0)
        
    def reset_all_facilities_force(self):
        self.log.info(f"强制复位所有设备：{self.flask_state}")
        CommandParser.wait_input("parser","请确认设备已")
        if self.flask_state == 2:
            self.name_put('sanjinshaoping_support_put')
        elif self.flask_state == 1:
            self.fr5_A.check_place_move()
            self.fr5_C.check_place_move()
            self.move_shaoping_C2support()
        self.bath_over()
        self.HN_init()
                

    def confirm_safety(self, text:str='ok?'):
        if self.should_safe:
            CommandParser.wait_input("parser", text)


    def pot_wash(self):
        Flowdisplay.update_process_display_dict(Process='冲洗抽滤', Action='', Info={})
        self.name_catch("sanjinshaoping_support")
        self.move_wash('sanjinshaoping_wash_1', 0)
        self.move_wash('sanjinshaoping_wash_2', 1)
        self.move_wash('sanjinshaoping_wash_1', 2)
        self.name_put("sanjinshaoping_support")
    
    def bath_update(self):
        Flowdisplay.update_process_display_dict(Process='冲洗抽滤', Action='', Info={})

    def bath_wash(self):
        Flowdisplay.update_process_display_dict(Process='冲洗抽滤', Action='', Info={})
        # self.temp_off()
        self.bath_catch('bath_fr5_catch')
        self.move_wash('sanjinshaoping_wash_1', 0)
        self.move_wash('sanjinshaoping_wash_2', 1)
        self.move_wash('sanjinshaoping_wash_3', 2)
        self.move_wash('sanjinshaoping_wash_1', 3)
        self.bath_put('bath_fr5_put')
        # self.temp_on()

    def move_wash(self, wash_place, index):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[wash_place])
        Info = {
            '冲洗位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process='冲洗抽滤', Action='冲洗抽滤', Info=Info)
        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        xyz_horizon = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]
        desc_pre = list(map(lambda x, y: x + y, xyz_horizon, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        dest_horizon = xyz_horizon + obj_statu['catch_direction']

        #移动到准备位置
        self.fr5_A.move_to_desc(desc_pre, vel=self.default_speed)
        time.sleep(1)

        #移动到下方位置
        self.fr5_A.move_to_desc(dest_horizon, vel=self.default_speed)
        time.sleep(1)

        #上升
        dest_safe = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(dest_safe, vel=self.default_put_speed)
        time.sleep(1)
        self.confirm_safety('safe?')
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['second_height']] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(dest, vel=self.default_put_speed)
        time.sleep(1)
        
        self.confirm_safety()

        self.height_level = 0

        def move_to_level(level = 0):
            dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['second_height'] - level * 2.0] + obj_statu['catch_direction']
            self.fr5_A.move_to_desc(dest, vel=self.default_put_speed)
            self.height_level = level
            Info = {
                '当前高度档位': self.height_level
            }
            Flowdisplay.update_process_display_dict(Process=None, Action=None, Info=Info)
            

        def wait_with_skip(seconds):
            start_time = time.time()
            end_time = start_time + seconds
            stop_flag = threading.Event()

            def input_thread():
                while not stop_flag.is_set():
                    try:
                        user_input = CommandParser.wait_input("parser", f"输入 'q' 跳过, 或 0-5 调整高度 (当前档位：{self.height_level})").strip().lower()
                        if stop_flag.is_set():
                            break
                        if user_input == 'q':
                            stop_flag.set()
                            break
                        elif user_input in ['0', '1', '2', '3', '4', '5']:
                            move_to_level(int(user_input))
                        else:
                            self.log.warning("输入无效，请输入 'q' 或 0-5")
                    except:
                        break

            t = threading.Thread(target=input_thread, daemon=True)
            t.start()

            while time.time() < end_time:
                if stop_flag.is_set():
                    self.log.info("跳过等待")
                    break
                time.sleep(1)
                print(f"\r剩余时间: {int(end_time - time.time())} s", end='', flush=True)
                Info = {
                    '当前高度档位': self.height_level,
                    '剩余时间 (秒)': int(end_time - time.time())
                }
                Flowdisplay.update_process_display_dict(Process=None, Action=None, Info=Info)
            
            stop_flag.set()

        def filter_process_A_new():
            """
            抽滤过程A
            """
            Flowdisplay.update_process_display_dict(Process='冲洗抽滤', Action='抽滤', Info={})
            while True:
                user_input = CommandParser.wait_input("parser",f"输入 0-5 调整高度, 或输入 q 进入抽滤 (当前档位：{self.height_level})").strip().lower()
                if user_input == 'q':
                    break
                elif user_input in ['0', '1', '2', '3', '4', '5']:
                    move_to_level(int(user_input))
                else:
                    self.log.warning("输入无效，请输入 'q' 或 0-5")
            out = True
            volume_t = 500.0
            while out == True:
                self.log.info(f"抽滤{volume_t}s")
                self.filter.pump_control_name("pump", 1)# 泵启动
                wait_with_skip(volume_t)
                self.filter.pump_control_name("pump", 0)
                volume_t = 500.0
                while True:
                    user_input = CommandParser.wait_input("parser",f"是否继续抽滤？(y/n), 或输入 0-5 调整高度 (当前档位：{self.height_level})").strip().lower()
                    if user_input == 'y':
                        break
                    elif user_input == 'n':
                        out = False
                        break
                    elif user_input in ['0', '1', '2', '3', '4', '5']:
                        move_to_level(int(user_input))
                    else:
                        self.log.warning("输入无效，请输入 'y' 或 'n' 或 0-5")

            self.log.info("抽滤过程A完成")

        def filter_process_E():
            for _ in range(8):
                move_to_level(10)
                time.sleep(1)
                move_to_level(5)
                time.sleep(1)

        # todo
        if index == 0:
            filter_process_A_new()
        elif index == 1:
        #     self.filter.filter_process_B(ParamTuple.HCl_volume_wash)
            self.filter.filter_process_B_new(ParamTuple.CH3CN_volume_add)
        elif index == 2:
            self.filter.filter_process_C(ParamTuple.water_volume_wash)
        elif index == 3:
            filter_process_E()
            # self.filter.filter_process_D_new(ParamTuple.CH3CN_volume_add)
            
        Info = {
            '冲洗位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process='冲洗抽滤', Action='冲洗抽滤', Info=Info)

        #移动到下方位置
        self.fr5_A.move_to_desc(dest_safe, vel=self.default_put_speed)
        time.sleep(1)
        self.confirm_safety('liquid ok?')

        self.fr5_A.move_to_desc(dest_horizon, vel=self.default_put_speed)
        time.sleep(1)

        if index == 0:
            pass
        elif index == 1:
            self.filter.filter_process_B_N()
        elif index == 2:
            self.filter.filter_process_C_N()
        elif index == 3:
            pass
        #     self.filter.filter_process_D_N()

        #移动到准备位置
        self.fr5_A.move_to_desc(desc_pre, vel=self.default_speed)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)


    def add_liquid_bath(self, liquid_name):
        """
        添加液体并设置水浴温度
        :param liquid_name: 液体名称
        """
        Flowdisplay.update_process_display_dict(Process=liquid_name + '液体进料', Action='', Info={})

        self.fr5_C.move_to_safe_catch(1)

        config = self.liquid_config.get(liquid_name)
        if not config:
            raise ValueError(f"未知液体: {liquid_name}")

        # 设置水浴温度
        # self.bath_writetmp(config['temp'])

        # 计算体积（如果体积是函数，则调用函数计算）
        volume = config['volume']

        # 添加液体
        if config['wash']:
            self.add_liquid(liquid_name, config['rpm'], volume, wash=True)
        else:
            self.add_liquid(liquid_name, config['rpm'], volume)

    def name_catch(self, name:str, test_tube_add:bool = False):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '抓取位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂抓取', Info=Info)

        
        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        self.confirm_safety()

        self.fr5_A.catch()

        self.fr5_A.data_dict["gripper_contain"] = name #用于输出夹持的物品信息

        time.sleep(1)
        
        if test_tube_add:
            with self.add_Solid:
                self.add_Solid.clip_open()
                self.tube_state = 0
                self.add_Solid.data_dict["gripper_contain"] = ""
                self.fr5_A.data_dict["gripper_contain"] = name
            time.sleep(1)

        #抬起
        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=self.default_put_speed)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)
        
    def name_put(self, name:str, test_tube_add:bool = False):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '放置位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂放置', Info=Info)

        # #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])
        obj_statu['destination'][2] += obj_statu['put_offset']

        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, dest, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        if test_tube_add:
            with self.add_Solid:
                self.add_Solid.clip_open()

        self.confirm_safety()

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=self.default_put_speed)

        if test_tube_add:
            self.fr5_A.gripper_30()
            with self.add_Solid:
                self.add_Solid.clip_close()
                self.tube_state = 1
                self.add_Solid.data_dict["gripper_contain"] = name
                self.fr5_A.data_dict["gripper_contain"] =""#用于输出夹持的物品信息
            self.confirm_safety()

        self.fr5_A.put()

        self.fr5_A.data_dict["gripper_contain"] =""#用于输出夹持的物品信息

        time.sleep(1)

        #移动出去
        self.fr5_A.move_by(obj_statu['catch_pre_xyz_offset'][0], obj_statu['catch_pre_xyz_offset'][1], obj_statu['catch_pre_xyz_offset'][2], vel=self.default_speed)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)

    def name_pour(self, name:str):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '倾倒位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='固体倾倒', Info=Info)

        # #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        self.fr5_C.move_to_safe_catch(2)

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['pour_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #靠近
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #旋转30度
        self.fr5_A.move_by(0,0,0,0,40.0,0)

        self.fr5_A.pour(22.0, 75.0, direction=-2, max_angle=90)

        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=self.default_put_speed)
        time.sleep(1)

        #计算物体位置
        desc_pos_aim = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)

        #移动出去
        self.fr5_A.move_by(obj_statu['pour_pre_xyz_offset'][0], obj_statu['pour_pre_xyz_offset'][1], obj_statu['pour_pre_xyz_offset'][2], vel=self.default_speed)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)

        self.fr5_C.move_to_safe_catch(1)

    def fr5_C_pour(self, name='beaker_pour'):
        obj_statu = copy.deepcopy(self.fr5_C.obj_status[name])
        Info = {
            '倾倒位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='产物倾倒', Info=Info)

        if self.fr5_A.now_place == 7:
            self.fr5_A.move_to_safe_catch(3)

        self.fr5_C.move_to_safe_catch(4)

        #移动到安全准备位置
        dest = [obj_statu['safe_destination'][0], obj_statu['safe_destination'][1], obj_statu['safe_destination'][2]]
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_C.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #旋转
        self.fr5_C.move_by(0,0,0,0,-40.0,0)
        time.sleep(1)

        #下降
        self.fr5_C.move_by(0, 0, -obj_statu['put_height'], vel=self.default_put_speed)
        time.sleep(1)

        #移动到准备位置
        self.fr5_C.move_by(obj_statu['pour_move'], 0, 0)
        time.sleep(1)

        self.fr5_C.move_by(0,0,0,0,-5.0,0)
        time.sleep(1)
        
        pour_wait_time_1 = 30
        pour_wait_time_2 = 10

        self.fr5_C.pour(130.0, -100.0, direction=2, max_angle=15, rate_percentage=10, shake=0)
        time.sleep(pour_wait_time_1)

        self.fr5_C.move_by(-20.0, 0, 0, vel=self.default_put_speed)

        self.fr5_C.pour(130.0, -100.0, direction=2, max_angle=7, rate_percentage=10, shake=0)
        time.sleep(pour_wait_time_1)
        self.fr5_C.pour(130.0, -100.0, direction=2, max_angle=8, rate_percentage=10, shake=0)
        time.sleep(pour_wait_time_2)
        self.fr5_C.pour(130.0, -100.0, direction=2, max_angle=10, rate_percentage=10, shake=0)
        time.sleep(pour_wait_time_2)
        self.fr5_C.pour(130.0, -100.0, direction=2, max_angle=15, rate_percentage=10, shake=0)
        time.sleep(pour_wait_time_2)

        self.fr5_C.move_by(20.0, 0, 0, vel=self.default_put_speed)

        self.fr5_C.move_by(obj_statu['pour_move_back'], 0, 0, vel=self.default_put_speed)
        time.sleep(1)

        self.fr5_C.move_by(0,0,0,0,-10.0,0)
        time.sleep(1)

        self.fr5_C.move_by(0, 0, obj_statu['wash_height'], vel=self.default_put_speed)
        time.sleep(1)

        self.fr5_C.move_by(-obj_statu['wash_move'], 0, 0, vel=self.default_put_speed)
        time.sleep(1)

        self.add_Liquid.add_liquid('CH3CH', 150, 10)
        time.sleep(5)

        self.fr5_C.move_by(obj_statu['wash_move'], 0, 0, vel=self.default_put_speed)
        time.sleep(1)

        #移动到安全准备位置
        dest = [obj_statu['safe_destination'][0], obj_statu['safe_destination'][1], obj_statu['safe_destination'][2] + obj_statu['put_height']]
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_C.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #移动到安全位置
        self.fr5_C.move_to_desc(self.fr5_C.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)

        self.fr5_C.move_to_safe_catch(0)


    def bath_catch(self, name:str):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '交接单位' : '三颈烧瓶',
            '交接方向' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂交接', Info=Info)
        
        self.fr5_C.move_to_safe_catch(0)

        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=self.default_speed)
        time.sleep(1)

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_put_speed)
        time.sleep(1)

        self.fr5_A.gripper_15()
        time.sleep(1)

        self.confirm_safety()

        self.fr5_C.gripper_15()
        time.sleep(1)
        self.fr5_A.catch()
        time.sleep(1)
        self.fr5_C.put()

        self.fr5_C.data_dict["gripper_contain"] =""#用于输出夹持的物品信息

        time.sleep(1)
        

        #移动到准备位置
        desc_pos_aim_xyz = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['bath_pre_offset']))
        desc_pos_aim_pre_2 = desc_pos_aim_xyz + obj_statu['catch_direction']
        desc_pos_aim_pre_1 = list(map(lambda x, y: x + y, desc_pos_aim_xyz, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre_2, vel=self.default_speed)
        time.sleep(1)
        self.fr5_A.move_to_desc(desc_pos_aim_pre_1, vel=self.default_speed)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)

        if self.facility_emergency:
            self.log.error("检测到紧急停止，取消烧瓶状态位改变")
        else:
            self.flask_state = 2

    def bath_put(self, name:str):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '交接单位' : '三颈烧瓶',
            '交接方向' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂交接', Info=Info)

        self.fr5_C.move_to_safe_catch(0)

        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim_xyz = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['bath_pre_offset']))
        desc_pos_aim_pre_2 = desc_pos_aim_xyz + obj_statu['catch_direction']
        desc_pos_aim_pre_1 = list(map(lambda x, y: x + y, desc_pos_aim_xyz, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre_1, vel=self.default_speed)
        time.sleep(1)
        self.fr5_A.move_to_desc(desc_pos_aim_pre_2, vel=self.default_speed)
        time.sleep(1)

        self.confirm_safety()

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        self.fr5_C.gripper_15()
        time.sleep(1)

        self.confirm_safety()

        self.fr5_A.gripper_15()
        time.sleep(1)
        self.fr5_C.catch()

        self.fr5_C.data_dict["gripper_contain"] =name#用于输出夹持的物品信息

        time.sleep(1)
        self.fr5_A.put()
        time.sleep(1)

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=self.default_speed)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)

        if self.facility_emergency:
            self.log.error("检测到紧急停止，取消烧瓶状态位改变")
        else:
            self.flask_state = 1

    def bath_mix(self):

        def wait_with_skip(seconds):
            start_time = time.time()
            end_time = start_time + seconds
            stop_flag = threading.Event()

            def input_thread():
                while not stop_flag.is_set():
                    try:
                        user_input = CommandParser.wait_input("parser", f"输入 'q' 跳过").strip().lower()
                        if stop_flag.is_set():
                            break
                        if user_input == 'q':
                            stop_flag.set()
                            break
                        else:
                            self.log.warning("输入无效，请输入 'q' ")
                    except:
                        break

            t = threading.Thread(target=input_thread, daemon=True)
            t.start()

            while time.time() < end_time:
                if stop_flag.is_set():
                    self.log.info("跳过等待")
                    break
                time.sleep(1)
                print(f"\r剩余时间: {int(end_time - time.time())} s", end='', flush=True)
                Info = {
                    '剩余时间 (秒)': int(end_time - time.time())
                }
                Flowdisplay.update_process_display_dict(Process=None, Action='水浴搅拌', Info=Info)
            
            stop_flag.set()

        Flowdisplay.update_process_display_dict(Process='水浴搅拌', Action='水浴搅拌', Info={})
        self.bath_put('bath_fr5_put')
        self.fr5_C.move_to_safe_catch(1)
        wait_with_skip(30)
        self.fr5_C.move_to_safe_catch(0)
        wait_with_skip(30)
        self.bath_catch('bath_fr5_catch')
        

    def add_liquid(self, name:str, rpm = 150, volume = 0.0, wash = False, name_space='add_liquid_mode_place', volume_batch = 0.1):
        Flowdisplay.update_process_display_dict(Process=name + '液体进料', Action='', Info={})
        self.fr5_C.move_to_safe_catch(1)

        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '抓取位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂抓取', Info=Info)

        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        self.fr5_A.gripper_half()

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        self.confirm_safety()

        self.fr5_A.catch()
        time.sleep(1)

        #抬起
        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=self.default_speed)
        time.sleep(1)

        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name_space])
        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=self.default_speed)
        time.sleep(1)

        if wash==False:
            self.add_Liquid.add_liquid(name, rpm, volume)
            time.sleep(1)
        else:
            stop_event = threading.Event()
            t = -1
            dx = [1, 0, -2, 0, 1]
            dy = [0, 1, 0, -1, 0]

            def add_liquid_thread():
                self.add_Liquid.add_liquid(name, rpm, volume)
                stop_event.set()  # 通知主线程停止移动

            thread_add_liquid = threading.Thread(target=add_liquid_thread, daemon=True)
            thread_add_liquid.start()

            self.fr5_A.move_by(0, -obj_statu['wash_r'], 0)

            while not stop_event.is_set():
                t = (t + 1) % 5
                self.fr5_A.move_by(dx[t] * obj_statu['wash_r'], dy[t] * obj_statu['wash_r'])
                time.sleep(0.5)

            thread_add_liquid.join()

            obj_statu = copy.deepcopy(self.fr5_A.obj_status[name_space])
            dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2]]
            desc_pos_aim = dest + obj_statu['catch_direction']
            self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)


        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=self.default_speed)

        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '放置位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂放置', Info=Info)
        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        # #移动到准备位置
        # self.fr5_A.move_to_desc(desc_pos_aim_mid, vel=self.default_speed)
        # time.sleep(1)

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=self.default_speed)
        self.fr5_A.gripper_half()
        time.sleep(1)

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=self.default_speed)
        time.sleep(1)
        self.fr5_A.put()

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)


    def temp_catch(self, name, shaoping=False):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '抓取位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂抓取', Info=Info)

        
        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=self.default_speed)
        time.sleep(1)

        self.fr5_A.gripper_30()
        time.sleep(1)

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        self.confirm_safety()

        self.fr5_A.catch()
        self.fr5_A.data_dict["gripper_contain"] = name #用于输出夹持的物品信息
        time.sleep(1)

        #抬起
        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=self.default_put_speed)
        time.sleep(1)

        if shaoping==True:
            #移动到准备位置
            desc_pos_aim_pre_hei = list(map(lambda x, y: x + y, desc_pos_aim_pre, [0,0, obj_statu['put_height'],0,0,0]))
            self.fr5_A.move_to_desc(desc_pos_aim_pre_hei, vel=self.default_speed)
            time.sleep(1)

    def temp_put(self, name):
        obj_statu = copy.deepcopy(self.fr5_A.obj_status[name])
        Info = {
            '放置位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂放置', Info=Info)

        obj_statu['destination'][2] += obj_statu['put_offset']

        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, dest, obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=self.default_speed)
        time.sleep(1)
        self.confirm_safety()

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=self.default_put_speed)
        time.sleep(1)

        self.fr5_A.gripper_30()
        time.sleep(1)
        self.fr5_A.data_dict["gripper_contain"] =""#用于输出夹持的物品信息

        #移动出去
        self.fr5_A.move_by(obj_statu['catch_pre_xyz_offset'][0], obj_statu['catch_pre_xyz_offset'][1], obj_statu['catch_pre_xyz_offset'][2], vel=self.default_speed)
        time.sleep(1)

        self.fr5_A.put()

        #移动到安全位置
        self.fr5_A.set_nowplace(obj_statu['safe_place_id'])
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=self.default_speed)
        time.sleep(1)

    def temp_on(self):
        self.fr5_C.move_to_safe_catch(3)
        self.temp_catch('temp_support')
        self.temp_put('temp_place')
        self.fr5_A.move_to_safe_catch(3)
        self.temp_state = 1
        # self.temp_start()

    def temp_off(self):
        self.fr5_C.move_to_safe_catch(3)
        # self.temp_over()
        self.temp_catch('temp_place', shaoping=True)
        self.temp_put('temp_support')
        self.fr5_A.move_to_safe_catch(3)
        self.temp_state = 0

    def temp_start(self):
        # 如果已有线程在运行，先停止它
        if self.thermometer_thread and self.thermometer_thread.is_alive():
            self.temp_over()
        
        # 重置停止事件
        self.thermometer_stop_event.clear()
        
        def thermometer_thread():
            while not self.thermometer_stop_event.is_set():
                try:
                    self.thermometer.read_temp()
                    # 添加短暂等待，避免过于频繁的读取
                    if not self.thermometer_stop_event.wait(0.5):  # 等待0.1秒或直到停止事件被设置
                        continue
                    else:
                        break
                except Exception as e:
                    self.log.error(f"温度计读取出错: {e}")
                    break

        self.thermometer_thread = threading.Thread(target=thermometer_thread, daemon=True)
        self.thermometer_thread.start()

    def temp_over(self):
        # 设置停止事件，通知线程退出
        if hasattr(self, 'thermometer_stop_event'):
            self.thermometer_stop_event.set()
        
        # 等待线程结束
        if hasattr(self, 'thermometer_thread') and self.thermometer_thread and self.thermometer_thread.is_alive():
            self.thermometer_thread.join(timeout=4.0)  # 最多等待4秒
            if self.thermometer_thread.is_alive():
                self.log.warning("温度计线程未能在4秒内正常退出")
            else:
                self.log.info("温度计线程已成功停止")
        
        self.thermometer_thread = None
        self.thermometer.update_data_dict(temperature='--')
    
    def add_solid(self, gram:float, tube_from:str, beaker_from:str, test_tube_add_place:str='test_tube_add_place', beaker_add_place:str='beaker_add_place', pour_place:str='bath_pour_place', batch_gram_max:float = 0.6, min_unit: float = 0.01):
        
        if self.solid_config:
            gram = self.solid_config
        
        # --- 内部辅助函数：根据剩余重量计算加料计划 ---
        # 输入：remaining_gram (剩余需加重量)
        # 输出：(plan_list, num_steps) -> ([0.4, 0.4], 2)
        def calculate_plan(remaining_gram):
            if remaining_gram <= min_unit / 2: # 误差范围内视作完成
                return [], 0
            
            total_units = int(round(remaining_gram / min_unit))
            max_b_units = int(round(batch_gram_max / min_unit))
            
            # 防止除零错误
            if max_b_units == 0: max_b_units = 1 

            # 计算需要分几次
            num = (total_units + max_b_units - 1) // max_b_units
            
            # 计算基础量和余数量，尽可能平均分配
            base = total_units // num
            rem = total_units % num
            
            plan_int = [base + 1] * rem + [base] * (num - rem)
            plan_list = [round(w * min_unit, 6) for w in plan_int]
            
            return plan_list, num

        # --- 内部辅助函数：更新UI信息 ---
        def get_process_info(current_step_idx, weighed_total, added_total, plan_list, history_list):
            # 计算显示的规划字符串：已完成的(带括号) + 待进行的
            # 例如: "(0.70) + 0.40, 0.40"
            history_str = " + ".join([f"({h:.2f})" for h in history_list])
            future_str = ", ".join([f"{w:.2f}" for w in plan_list])
            
            if history_str and future_str:
                display_plan = f"{history_str} + {future_str} g"
            elif history_str:
                display_plan = f"{history_str} g (Finished)"
            else:
                display_plan = f"{future_str} g"

            # 动态计算总次数：历史次数 + 剩余计划次数
            total_predicted_steps = len(history_list) + len(plan_list)
            
            return {
                '总加料重量': f'{gram} g',
                '之前总计称量重量': f'{weighed_total:.2f} g',
                '之前总计加料重量': f'{added_total:.2f} g',
                '加料规划': display_plan,
                '预计加料次数': total_predicted_steps,
                '当前加料次数': current_step_idx
            }
        
        Flowdisplay.update_process_display_dict(Process='固体进料', Action='', Info={})

        # --- 初始化状态变量 ---
        current_weighed = 0.0  # 当前累计称量出的重量 (真实值)
        current_added = 0.0    # 当前累计倒入反应釜的重量
        history_weights = []   # 记录每次真实加料的重量历史
        
        # 初始规划
        remaining_gram = gram
        current_plan, _ = calculate_plan(remaining_gram)
        
        # 初始UI显示
        Process_Info = get_process_info(1, current_weighed, current_added, current_plan, history_weights)
        Flowdisplay.update_process_display_dict(Process='固体进料', Action=None, Info=None, Process_Info=Process_Info)

        # --- 设备准备动作 ---
        self.name_catch_and_put(tube_from, test_tube_add_place, test_tube_add_catch = False, test_tube_add_put = True)
        self.name_catch_and_put(beaker_from, beaker_add_place, test_tube_add_catch = False, test_tube_add_put = False)

        # --- 动态加料循环 ---
        # 只要还有剩余重量没加完，就继续循环
        while True:
            # 1. 检查是否完成
            remaining_gram = gram - current_weighed
            # 设置一个极小的公差，避免浮点数精度问题导致无限循环 (例如小于半个最小单位即视为完成)
            if remaining_gram <= min_unit / 2:
                break
            
            # 2. 重新规划 (Re-planning)
            # 每次循环开始都根据最新的剩余重量计算接下来的计划
            # 举例：目标1.5，第一次想加0.5但实际加了0.7，remaining变为0.8，这里会算出 [0.4, 0.4]
            plan_list, _ = calculate_plan(remaining_gram)
            
            if not plan_list: # 防止异常情况
                break
                
            target_this_time = plan_list[0] # 取出当前这一步的目标重量
            
            # 更新UI：准备加料
            Process_Info = get_process_info(len(history_weights) + 1, current_weighed, current_added, plan_list, history_weights)
            Flowdisplay.update_process_display_dict(Process='固体进料', Action='正在加料', Info=None, Process_Info=Process_Info)

            # 3. 执行加料 (Dosing)
            with self.add_Solid:
                self.add_Solid.add_solid_series(target_this_time)
                this_real_weight = self.add_Solid.data_dict['weight_now']
                if this_real_weight < target_this_time:
                    this_real_weight = target_this_time
                self.add_Solid.tube_ver()
            
            # 4. 更新数据状态
            current_weighed += this_real_weight
            history_weights.append(this_real_weight)
            
            # 更新UI：加料完成，准备倾倒
            # 注意：这里再次重新计算剩余计划，以便UI显示 "总次数" 的变化
            # 例如：本来剩0.8要分2次，结果这步直接加了0.8，下次循环就会直接退出，总次数自动减1
            remaining_after_step = gram - current_weighed
            future_plan_check, _ = calculate_plan(remaining_after_step)
            
            Process_Info = get_process_info(len(history_weights), current_weighed, current_added, future_plan_check, history_weights)
            Flowdisplay.update_process_display_dict(Process='固体进料', Action='准备倾倒', Info=None, Process_Info=Process_Info)

            # 5. 执行倾倒流程 (Pouring)
            self.name_catch(beaker_add_place)
            self.name_pour(pour_place)
            
            # 假设倾倒完全，已加料重量 = 已称量重量
            current_added = current_weighed
            
            # 更新UI：倾倒完成
            Process_Info = get_process_info(len(history_weights), current_weighed, current_added, future_plan_check, history_weights)
            Flowdisplay.update_process_display_dict(Process='固体进料', Action='倾倒完成', Info=None, Process_Info=Process_Info)

            # 6. 判断是否需要放回原处还是放回加料位
            # 如果还有剩余重量需要加 (future_plan_check 非空)，则放回 beaker_add_place 继续循环
            # 如果已经加完了，则放回 beaker_from (原始位置) 并退出循环
            if len(future_plan_check) > 0 and remaining_after_step > min_unit / 2:
                self.name_put(beaker_add_place)
            else:
                self.name_put(beaker_from) # 结束，归位
                break
        
        # self.name_catch_and_put(test_tube_add_place, tube_from, test_tube_add_catch = True, test_tube_add_put = False)
        
        Flowdisplay.update_process_display_dict(Process='固体进料', Action='完成', Info=None, Process_Info={})
        self.add_liquid_config_change(current_added)

    
    def name_catch_and_put(self, name1:str, name2:str, test_tube_add_catch:bool = False, test_tube_add_put:bool = False):
        if test_tube_add_catch:
            self.name_catch(name1, test_tube_add=True)
        else:
            self.name_catch(name1)
        if test_tube_add_put:
            self.name_put(name2, test_tube_add=True)
        else:
            self.name_put(name2)

    def fr5_gripper_activate(self):
        self.fr5_A.reset_gripper()

    def fr5_Go_to_start_zone_0(self):
        self.fr5_A.Go_to_start_zone_0()

    def bath_open(self):
        Flowdisplay.update_process_display_dict(Process=None, Action='水浴锅开启', Info={})
        self.bath.power_ctr(1)

    def bath_start(self):
        Flowdisplay.update_process_display_dict(Process='控制水浴锅', Action='水浴锅控温开启', Info={})
        self.bath.power_ctr(1)
        self.bath.mix_ctr(1)
        self.bath.circle_ctr(1)# 允许circle
        # self.bath.hot_ctr(1)# 加热
        self.bath.cold_ctr(1)# 允许制冷

    def bath_over(self):
        Flowdisplay.update_process_display_dict(Process='控制水浴锅', Action='水浴锅控温关闭', Info={})
        self.bath.mix_ctr(0)
        self.bath.circle_ctr(0)# 禁止circle
        self.bath.hot_ctr(0)# 禁止加热
        self.bath.cold_ctr(0)# 禁止制冷

    def bath_close(self):
        Flowdisplay.update_process_display_dict(Process='控制水浴锅', Action='水浴锅关闭', Info={})
        self.bath.power_ctr(0)

    def bath_writetmp(self, tmp:float, close_hot = 1):
        self.fr5_C.move_to_safe_catch(1)
        self.bath.interactable_writetmp(tmp, close_hot)

    def interactable_countdown(self, seconds:float):
        Info = {
            '剩余时间': '',
        }
        Flowdisplay.update_process_display_dict(Process='持续反应过程', Action='等待化学反应', Info=Info)
        
        start_time = time.time()
        end_time = start_time + seconds
        
        # 用于控制是否停止的标志
        stop_flag = threading.Event()
        
        def input_thread():
            while not stop_flag.is_set():
                try:
                    user_input = CommandParser.wait_input("parser", "输入 'q' 跳过倒计时...")
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
        
        while time.time() < end_time:
            # 检查是否收到停止信号
            if stop_flag.is_set():
                self.log.info("手动停止计时")
                break
                
            # 计算剩余时间
            now = time.time()
            remaining_time = end_time - now
            
            if remaining_time <= 0:
                break
                
            # 计算预计完成时间
            finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
            
            # 使用 \r 回到行首覆盖输出，end='' 避免换行
            print(f"\r剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}", end='', flush=True)
            
            Info = {
                '剩余时间': str(int(remaining_time)) + ' s',
            }
            Flowdisplay.update_process_display_dict(Process=None, Action='化学反应', Info=Info)

            self.bath.read_temp()
            
            # 短暂等待后继续监控
            time.sleep(1)
        
        stop_flag.set()  # 确保输入线程结束
        
        if time.time() >= end_time:
            self.log.info("时间到")
        
        total_time = time.time() - start_time
        self.log.info(f"倒计时结束，总耗时: {int(total_time)} 秒")

        time.sleep(0.5)

    def fr5A_init(self):
        Flowdisplay.update_process_display_dict(Process='HN机械臂初始化', Action='fr5_A初始化', Info={})
        self.fr5_A.fr5_init()

    def fr5C_init(self):
        Flowdisplay.update_process_display_dict(Process='HN机械臂初始化', Action='fr5_C初始化', Info={})
        self.fr5_C.fr5_init()

    def fr5_check_place(self):
        self.fr5_A.check_place_move()

    def HN_init(self):
        Flowdisplay.update_process_display_dict(Process='HN机械臂初始化', Action='', Info={})
        self.fr5A_init()
        self.fr5C_init()
        self.bath_open()
        self.add_solid_init()

    def add_solid_init(self):
        Flowdisplay.update_process_display_dict(Process='固体进料器初始化', Action='', Info={})
        with self.add_Solid:
            self.add_Solid.tube_ver()
            self.add_Solid.clip_open()

    def add_liquid_init(self):
        self.add_liquid_config_init()
        Flowdisplay.update_process_display_dict(Process='液体进料器初始化', Action='', Info={})
        self.add_Liquid.liquid_back('HCl')
        self.add_Liquid.liquid_back('KMnO4')
        self.add_Liquid.liquid_back('H2O2')
        self.add_Liquid.liquid_back('N2H4')
        self.filter.filter_process_B_N()
        self.filter.filter_process_C_N()
        self.filter.filter_process_D_N()
        
    def add_liquid_config_init(self):
        Flowdisplay.update_process_display_dict(Process='配置应用中', Action='', Info={})
        self.liquid_config['HCl']['volume'] = ParamTuple.HCl_volume_add * 0.8
        self.liquid_config['HCl_wash']['volume'] = ParamTuple.HCl_volume_add * 0.2
        self.liquid_config['KMnO4']['volume'] = ParamTuple.KMnO4_volume_add
        self.liquid_config['H2O2']['volume'] = ParamTuple.H2O2_volume_add
        self.liquid_config['N2H4']['volume'] = ParamTuple.N2H4_volume_add
        self.liquid_config['HCl']['rpm'] = ParamTuple.HCl_rpm
        self.liquid_config['HCl_wash']['rpm'] = ParamTuple.HCl_rpm
        self.liquid_config['KMnO4']['rpm'] = ParamTuple.KMnO4_rpm
        self.liquid_config['H2O2']['rpm'] = ParamTuple.H2O2_rpm
        self.liquid_config['N2H4']['rpm'] = ParamTuple.N2H4_rpm
        self.liquid_config['HCl']['temp'] = ParamTuple.HCl_temp
        self.liquid_config['HCl_wash']['temp'] = ParamTuple.HCl_temp
        self.liquid_config['KMnO4']['temp'] = ParamTuple.KMnO4_temp
        self.liquid_config['H2O2']['temp'] = ParamTuple.H2O2_temp
        self.liquid_config['N2H4']['temp'] = ParamTuple.N2H4_temp

    def add_liquid_config_change(self, CompoundC_solid_add):
        Flowdisplay.update_process_display_dict(Process='配置应用中', Action='', Info={})
        ParamTuple.HCl_volume_add *= CompoundC_solid_add / ParamTuple.CompoundC_solid_add # 浓盐酸
        ParamTuple.KMnO4_volume_add *= CompoundC_solid_add / ParamTuple.CompoundC_solid_add # 高锰酸钾添加量 
        ParamTuple.H2O2_volume_add *= CompoundC_solid_add / ParamTuple.CompoundC_solid_add # 双氧水添加量
        ParamTuple.N2H4_volume_add *= CompoundC_solid_add / ParamTuple.CompoundC_solid_add # 肼添加量
        ParamTuple.CH3CN_volume_add *= CompoundC_solid_add / ParamTuple.CompoundC_solid_add  # 乙腈添加量
        ParamTuple.HCl_volume_wash *= CompoundC_solid_add / ParamTuple.CompoundC_solid_add
        ParamTuple.water_volume_wash *= CompoundC_solid_add / ParamTuple.CompoundC_solid_add
        ParamTuple.CompoundC_solid_add = CompoundC_solid_add

        self.liquid_config['HCl_wash']['volume'] = ParamTuple.HCl_volume_add - self.liquid_config['HCl']['volume']
        self.liquid_config['KMnO4']['volume'] = ParamTuple.KMnO4_volume_add
        self.liquid_config['H2O2']['volume'] = ParamTuple.H2O2_volume_add
        self.liquid_config['N2H4']['volume'] = ParamTuple.N2H4_volume_add

    def add_solid_config_init(self):
        self.solid_config = ParamTuple.CompoundC_solid_add

    def move_shaoping_support2C(self):
        Flowdisplay.update_process_display_dict(Process='烧瓶转移 A to C', Action='', Info={})   
        self.name_catch('sanjinshaoping_support')
        self.bath_put('bath_fr5_put')
        # self.temp_on()


    def move_shaoping_C2support(self):
        Flowdisplay.update_process_display_dict(Process='烧瓶转移 C to A', Action='', Info={})
        # self.temp_off()
        self.bath_catch('bath_fr5_catch')
        self.name_put('sanjinshaoping_support_put')

    