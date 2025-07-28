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

class HN_SDK(Facility):
    type = "Chemistry OS SDK"
    name = "sdk"
    version = "1.0.0"
    description = "A software development kit for Chemistry OS."
    compound_c = 0.50
    liquid_config = {
        'HCl': {
            'temp': 0,
            'rpm': 100,
            'volume': lambda c: 26.8 * c,
            'reaction_time':0
        },
        'KMnO4': {
            'temp': 25,
            'rpm': 15,
            'volume': lambda c: 53.52 * c,
            'reaction_time':7200
        },
        'H2O2': {
            'temp': 0,
            'rpm': 30,
            'volume': lambda c: 20.0 * c,
            'reaction_time':1200
        },
        'CH3CN': {
            'temp': 25,
            'rpm': 30,
            'volume': 20.0,
            'reaction_time':0
        },
        'N2H4': {
            'temp': 25,
            'rpm': 30,
            'volume': 0.4854,
            'reaction_time':14400
        },
    }
    
    def __init__(self):
        super().__init__(name="sdk", type = HN_SDK.type)

        def get_facility_ref(name, expected_type):
            for facility in Facility.tuple_list:
                if facility[0] == name and isinstance(facility[3], expected_type):
                    # print(f"获取到 {name} 的引用，{facility[3]}")
                    return facility[3]  # 返回实例化的对象引用
            print(f"错误：对象 {name} 不存在于 Facility.tuple_list 中，或类型不匹配。")
            print(Facility.tuple_list)
            raise ValueError(f"对象 {name} 不存在于 Facility.tuple_list 中，或类型不匹配。")

        try:
            # 引用 Facility.tuple_list 中的对象，并提供默认类型
            self.fr5_A: Fr5Arm = get_facility_ref("fr5A", Fr5Arm)
            self.add_Liquid: PumpGroup = get_facility_ref("add_Liquid", PumpGroup)
            self.add_Solid: Add_Solid = get_facility_ref("add_Solid", Add_Solid)
            self.fr5_C: Fr5Arm = get_facility_ref("fr5C", Fr5Arm)
            self.bath: Bath = get_facility_ref("bath", Bath)
            # self.filter: Filter = get_facility_ref("filter", Filter)

        except ValueError as e:
            print(e)

    def cmd_init(self):
        self.parser.register("name_catch", self.name_catch, {"name":''}, "fr5 catch named place")
        self.parser.register("name_put", self.name_put, {"name":''}, "fr5 put named place")
        self.parser.register("name_pour", self.name_pour, {"name":''}, "fr5 pour named place")
        self.parser.register("bath_catch", self.bath_catch, {"name":''}, "fr5 bath catch")
        self.parser.register("bath_put", self.bath_put, {"name":''}, "fr5 bath put")
        self.parser.register("add_liquid", self.add_liquid, {"name":'', "rpm":150, "volume":0.0}, "add liquid to named place")
        self.parser.register("add_liquid_bath", self.add_liquid_bath, {"name":''}, "add liquid to named place and bath")
        self.parser.register("add_solid", self.add_solid, {"gram":0.0, "tube_from":'', "beaker_from":''}, "add solid to named place")  # 修正参数名
        self.parser.register("name_catch_and_put", self.name_catch_and_put, {"name1":'', "name2":''}, "fr5 catch name1 and put name2")
        self.parser.register("name_catch_pour_put", self.name_catch_pour_put, {"name1":'', "name2":'', "name3":''}, "catch, pour and put")
        self.parser.register("fr5_gripper_activate", self.fr5_gripper_activate, {}, "activate fr5 gripper")
        self.parser.register("fr5_Go_to_start_zone_0", self.fr5_Go_to_start_zone_0, {}, "fr5 go to start zone 0")
        self.parser.register("bath_open", self.bath_open, {}, "initialize bath")
        self.parser.register("bath_close", self.bath_close, {}, "close bath")
        self.parser.register("bath_writetmp", self.bath_writetmp, {"tmp":0.0}, "write temperature to bath")
        self.parser.register("interactable_countdown", self.interactable_countdown, {"seconds":0.0}, "start interactive countdown")
        self.parser.register("fr5A_init", self.fr5A_init, {}, "initialize fr5A")
        self.parser.register("fr5C_init", self.fr5C_init, {}, "initialize fr5C")
        self.parser.register("HN_init", self.HN_init, {}, "initialize HN")
        self.parser.register("move_shaoping_A2C", self.move_shaoping_A2C, {}, "move_shaoping_A2C")
        self.parser.register("move_shaoping_C2A", self.move_shaoping_C2A, {}, "move_shaoping_C2A")


    def pot_wash(self):
        self.name_catch("sanjinshaoping_support")
        self.move_wash('sanjinshaoping_wash_1', 0)
        self.move_wash('sanjinshaoping_wash_2', 1)
        self.move_wash('sanjinshaoping_wash_1', 2)
        self.name_put("sanjinshaoping_support")

    def bath_wash(self):
        self.bath_catch('bath_fr5_catch')
        self.move_wash('sanjinshaoping_wash_1')
        self.move_wash('sanjinshaoping_wash_2')
        self.move_wash('sanjinshaoping_wash_1')
        self.bath_put('bath_fr5_put')

    def move_wash(self, wash_place, index):
        obj_statu = self.fr5_A.obj_status[wash_place]
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
        self.fr5_A.move_to_desc(desc_pre, vel=10)
        time.sleep(1)

        #移动到下方位置
        self.fr5_A.move_to_desc(dest_horizon, vel=10)
        time.sleep(1)

        #上升
        dest_safe = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(dest_safe, vel=5)
        input('safe?')
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['second_height']] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(dest, vel=5)
        time.sleep(1)


        

        input('ok?')

        # todo
        if index == 0:
            self.filter.filter_process_A()
        elif index == 1:
            self.filter.filter_process_B()
        elif index == 2:
            self.filter.filter_process_C()

        input('filter ok?')


        #移动到下方位置
        self.fr5_A.move_to_desc(dest_horizon, vel=10)
        time.sleep(1)

        input('liquid ok?')
        
        #移动到准备位置
        self.fr5_A.move_to_desc(desc_pre, vel=10)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)


    def add_liquid_bath(self, liquid_name):
        """
        添加液体并设置水浴温度
        :param liquid_name: 液体名称
        """
        Flowdisplay.update_process_display_dict(Process='添加液体并反应', Action='', Info={})
        config = self.liquid_config.get(liquid_name)
        if not config:
            raise ValueError(f"未知液体: {liquid_name}")

        # 设置水浴温度
        self.bath_writetmp(config['temp'])

        # 计算体积（如果体积是函数，则调用函数计算）
        if callable(config['volume']):
            volume = config['volume'](self.compound_c)
        else:
            volume = config['volume']

        # 添加液体
        self.add_liquid(liquid_name, config['rpm'], volume)
        reaction_time = config['reaction_time']

        # 反应时间
        self.interactable_countdown(reaction_time)

    def name_catch(self, name:str, test_tube_add:bool = False):
        obj_statu = self.fr5_A.obj_status[name]
        Info = {
            '抓取位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂抓取', Info=Info)

        
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

        if test_tube_add:
            self.fr5_A.gripper_30()
            time.sleep(1)
            with self.add_Solid:
                self.add_Solid.clip_open()

        input('ok?')
        self.fr5_A.catch()
        time.sleep(1)

        #抬起
        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=10)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)
        
    def name_put(self, name:str, test_tube_add:bool = False):
        obj_statu = self.fr5_A.obj_status[name]
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
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)
        input('ok?')

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=5)

        if test_tube_add:
            self.fr5_A.gripper_30()
            with self.add_Solid:
                self.add_Solid.clip_close()
            input('ok?')

        self.fr5_A.put()

        time.sleep(1)

        #移动出去
        self.fr5_A.move_by(obj_statu['catch_pre_xyz_offset'][0], obj_statu['catch_pre_xyz_offset'][1], obj_statu['catch_pre_xyz_offset'][2], vel=10)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

    def name_pour(self, name:str):
        obj_statu = self.fr5_A.obj_status[name]
        Info = {
            '倾倒位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='固体倾倒', Info=Info)

        # #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #旋转30度
        self.fr5_A.move_by(0,0,0,0,-30.0,0)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=10)

        self.fr5_A.pour(24.1, 65.0)

        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=10)
        time.sleep(1)

        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        print(desc_pos_aim)
        time.sleep(1)

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

        # self.fr3_C.move_to_catch()

    def bath_catch(self, name:str):
        obj_statu = self.fr5_A.obj_status[name]
        Info = {
            '交接单位' : '三颈烧瓶',
            '交接方向' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂交接', Info=Info)

        self.fr5_C.move_to_catch()

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

        self.fr5_A.gripper_15()
        time.sleep(1)

        input('ok?')

        self.fr5_C.gripper_15()
        time.sleep(1)
        self.fr5_A.catch()
        time.sleep(1)
        self.fr5_C.put()
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
        Info = {
            '交接单位' : '三颈烧瓶',
            '交接方向' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂交接', Info=Info)

        self.fr5_C.move_to_catch()

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

        input('ok?')

        #靠近，完成抓取
        desc_pos_aim = obj_statu['destination'] + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        self.fr5_C.gripper_20()
        time.sleep(1)

        input('ok?')

        self.fr5_A.gripper_15()
        time.sleep(1)
        self.fr5_C.catch()
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

        self.fr5_C.move_to_shuiyu()

        obj_statu = self.fr5_A.obj_status[name]
        Info = {
            '抓取位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂抓取', Info=Info)

        #根据id确定安全位置, 移动到安全位置
        self.fr5_A.move_to_safe_catch(obj_statu['safe_place_id'])

        #移动到准备位置
        desc_pos_aim = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        self.fr5_A.gripper_half()

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
        time.sleep(1)

        self.add_Liquid.add_liquid(name, rpm, volume)
        time.sleep(1)

        self.fr5_A.move_by(0, 0, obj_statu['put_height'], vel=10)

        obj_statu = self.fr5_A.obj_status[name]
        Info = {
            '放置位置' : obj_statu['name']
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂放置', Info=Info)
        #计算物体位置
        dest = [obj_statu['destination'][0], obj_statu['destination'][1], obj_statu['destination'][2] + obj_statu['put_height']]

        #移动到放置位置上方
        desc_pos_aim = dest + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim, vel=10)
        time.sleep(1)

        #下降，完成放置
        self.fr5_A.move_by(0, 0, -obj_statu['put_height'], vel=10)
        self.fr5_A.gripper_half()
        time.sleep(1)

        #移动到准备位置
        desc_pos_aim_pre = list(map(lambda x, y: x + y, obj_statu['destination'], obj_statu['catch_pre_xyz_offset'])) + obj_statu['catch_direction']
        self.fr5_A.move_to_desc(desc_pos_aim_pre, vel=10)
        time.sleep(1)
        self.fr5_A.put()

        #移动到安全位置
        self.fr5_A.move_to_desc(self.fr5_A.safe_place[obj_statu['safe_place_id']], vel=10)
        time.sleep(1)

    def add_solid(self, gram:float, tube_from:str, beaker_from:str, test_tube_add_place:str='test_tube_add_place', beaker_add_place:str='beaker_add_place', pour_place:str='solid_pour_place'):
        Flowdisplay.update_process_display_dict(Process='固体进料', Action='', Info={})
        self.name_catch(tube_from)
        self.name_put(test_tube_add_place, test_tube_add=True)
        self.name_catch_and_put(beaker_from, beaker_add_place)

        with self.add_Solid:
            self.add_Solid.add_solid_series(gram)

        self.name_catch(test_tube_add_place, test_tube_add=True)
        self.name_put(tube_from)
        self.name_catch(beaker_add_place)
        self.name_pour(pour_place)
        self.name_put(beaker_from)
    
    def name_catch_and_put(self, name1:str, name2:str):
        self.name_catch(name1)
        self.name_put(name2)

    def name_catch_pour_put(self, name1:str, name2:str, name3:str):
        self.name_catch(name1)
        self.name_pour(name2)
        self.name_put(name3)

    def fr5_gripper_activate(self):
        self.fr5_A.reset_gripper()

    def fr5_Go_to_start_zone_0(self):
        self.fr5_A.Go_to_start_zone_0()

    def bath_open(self):
        Flowdisplay.update_process_display_dict(Process='控制水浴锅', Action='水浴锅开启', Info={})
        self.bath.power_ctr(1)
        self.bath.mix_ctr(1)
        self.bath.circle_ctr(1)# 允许circle
        self.bath.hot_ctr(1)# 加热
        self.bath.cold_ctr(1)# 允许制冷

    def bath_close(self):
        Flowdisplay.update_process_display_dict(Process='控制水浴锅', Action='水浴锅关闭', Info={})
        self.bath.mix_ctr(0)
        self.bath.circle_ctr(0)# 禁止circle
        self.bath.hot_ctr(0)# 禁止加热
        self.bath.cold_ctr(0)# 禁止制冷
        self.bath.power_ctr(0)

    def bath_writetmp(self, tmp:float):
        self.bath.interactable_writetmp(tmp)

    def interactable_countdown(self, seconds:float):
    # 用于控制是否继续计时的事件

        Info = {
            '剩余时间': '',
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='化学反应', Info=Info)
        
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
                Info = {
                    '剩余时间': remaining_time,
                }
                Flowdisplay.update_process_display_dict(Process=None, Action='化学反应', Info=Info)
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

    def fr5A_init(self):
        Flowdisplay.update_process_display_dict(Process=None, Action='fr5_A初始化', Info={})
        self.fr5_A.fr5_init()

    def fr5C_init(self):
        Flowdisplay.update_process_display_dict(Process=None, Action='fr5_C初始化', Info={})
        self.fr5_C.fr5_init()

    def fr5_check_place(self):
        self.fr5_A.fr5_check_place()

    def HN_init(self):
        Flowdisplay.update_process_display_dict(Process='HN机械臂初始化', Action='', Info={})
        self.fr5A_init()
        self.fr5C_init()

    def move_shaoping_A2C(self):
        Flowdisplay.update_process_display_dict(Process='烧瓶转移 A to C', Action='', Info={})
        self.name_catch('sanjinshaoping_support')
        self.bath_put('bath_fr5_put')


    def move_shaoping_C2A(self):
        Flowdisplay.update_process_display_dict(Process='烧瓶转移 C to A', Action='', Info={})
        self.bath_catch('bath_fr5_catch')
        self.name_put('sanjinshaoping_support')

    