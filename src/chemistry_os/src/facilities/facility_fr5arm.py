import datetime
import heapq
import json
import sys
import sys
import threading
sys.path.append('src/chemistry_os/src')
import lib.fairino.Robot as Robot
from user.zzp.simple_client import TCPClient
from user.zzp.unity import DeviceType,Gripper_status,Running_status,Weighing_status,Tube_position
import time
import math
import numpy as np
from facility import Facility
from structs import FacilityState
from exceptions import *
from facilities.flowdisplay import Flowdisplay
from utilities.utility_param import ParamUtils

class Fr5Arm(Facility):
    type = "fr5arm"
    default_speed = 20.0
    default_fr5C_speed = 10.0
    default_acc = 10.0
    default_circle_speed = 5.0
    default_circle_acc = 40.0
    default_start_pose = [0,-250,400,90,0,0]
    default_start_joint = [-45.548,-48.178,-126.989,-184.834,-43.048,0]
    angle_offset = 45.0
    saved_pose = [0,0,0,0,0,0]

    def __init__(self, name: str, ip: str,emergency_detect:bool=True):
        super().__init__(name, Fr5Arm.type)
        self.emergency_detect = emergency_detect
        self.emergency_detect_thread = None
        self.version = ""
        self.ip = ""
        self.can_gripper = False

        self.robot = Robot.RPC(ip)
        if self.name=='fr5A':
            self.position_file_path = "src/chemistry_os/src/facilities/location/fr5A.json"
        elif self.name=='fr5C':
            self.position_file_path = "src/chemistry_os/src/facilities/location/fr5C.json"

        with open(self.position_file_path, 'r') as file:
            text = json.load(file)
            self.obj_status = text['obj_status']
            self.safe_place = text['safe_place']
            self.graph = {int(k): {int(inner_k): inner_v for inner_k, inner_v in v.items()} for k, v in text['graph'].items()}
        
        self.obj_status_init()
        self.arm_init()
        self.start_emergency_detect()
        self.data_dict = {
            "joint_angles": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "gripper_position":100.0,
            "gripper_contain":"",
            "ip":None,
            "version":None
        }
        # 自动读取 __init__ 形参并保存到 init_dict
        self.init_dict = ParamUtils.get_init_params(self)
        

    def start_emergency_detect(self):
        if self.emergency_detect and self.emergency_detect_thread is None:
            try:
                self.emergency_detect_thread = threading.Thread(target=self.emergency_detect_func)
                self.emergency_detect_thread.daemon = True
                self.emergency_detect_thread.start()
            except Exception as e:
                self.log.error(f"安全检测线程启动失败: {e}")
                self.emergency_detect = False

    def emergency_detect_func(self):
    #检测机械臂急停标志位，检测到后将机械臂软件标签位设置为ERROR
        while self.emergency_detect:
            # print(self.robot.robot_state_pkg.EmergencyStop)
            if self.robot.robot_state_pkg.EmergencyStop and self.state != FacilityState.ERROR:
                self.log.error(f"{self.name}机械臂检测到急停，设置状态为ERROR")
                self.state = ParamUtils.set_facility_state(self.state,FacilityState.ERROR)
            time.sleep(0.03)
            # print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
            #输出时间戳 




    def data_dict_update(self):
        """
        更新机械臂数据
        """
        joint_angles = [round(self.robot.robot_state_pkg.jt_cur_pos[i], 2) for i in range(6)]
        data_dict_t = {
            "joint_angles": joint_angles,
            "gripper_position":self.robot.robot_state_pkg.gripper_position,
            "ip":self.ip,
            "version":self.version
        }
        self.data_dict.update(data_dict_t)

    def arm_init(self):
        ret, self.version = self.robot.GetSDKVersion()  # 查询SDK版本号
        if ret == 0:
            self.log.info(f"FR5机械臂SDK版本号为: {', '.join(self.version)}")
        else:
            self.log.info(f"FR5机械臂查询失败，错误码: {ret}")
        try:
            temp_ip = self.robot.GetControllerIP()  # 查询控制器IP
            if isinstance(temp_ip, tuple) and len(temp_ip) == 2:
                temp, ip_check = temp_ip
                if temp == 0:
                    self.log.info(f"FR5控制器IP :{ip_check}")
                    self.ip = ip_check
                else:
                    raise RuntimeError(f"FR5机械臂IP检查错误，错误码: {temp}")
            else:
                temp = temp_ip
                raise RuntimeError(f"FR5机械臂IP检查错误，错误码: {temp}")
        except RuntimeError as e:
            self.log.info(f"机械臂初始化失败: {e}")
            self.state = FacilityState.ERROR
            return

        self.initial_offset = [0, 0, 0, 0, 0, 0]  # 机械臂初始位置与世界坐标系原点的偏差
        self.open_up()

    def continue_facility(self):
        self.arm_init()

    def obj_status_init(self):
        for obj_name, obj_info in self.obj_status.items():
            # 检查是否存在 'catch_pre_offset' 键
            if 'catch_pre_offset' in obj_info and 'catch_direction' in obj_info:
                # 根据 'catch_pre_offset' 的值计算 'catch_pre_xyz_offset'

                if abs(obj_info['catch_direction'][2]+90)<0.1:
                    obj_info['catch_pre_xyz_offset'] = [obj_info['catch_pre_offset'], 0.0, 0.0]
                elif abs(obj_info['catch_direction'][2])<0.1:
                    obj_info['catch_pre_xyz_offset'] = [0.0, obj_info['catch_pre_offset'], 0.0]
                elif abs(obj_info['catch_direction'][2]-90)<0.1:
                    obj_info['catch_pre_xyz_offset'] = [-obj_info['catch_pre_offset'], 0.0, 0.0]
                elif abs(obj_info['catch_direction'][2]-180)<0.1:
                    obj_info['catch_pre_xyz_offset'] = [0.0, -obj_info['catch_pre_offset'], 0.0]

    def cmd_init(self):
        self.parser.register("moveto",self.move_to,
                            {
                            "x": 0.0, # 世界坐标系x
                            "y": 0.0, # 世界坐标系y
                            "z": 0.0, # 世界坐标系z
                            "r1": 0.0, # 末端姿态角度
                            "r2": 0.0, # 末端姿态角度
                            "r3": 0.0, # 末端姿态角度
                            "type": "MoveL", # 运动类型
                            "vel": self.default_speed, # 速度
                            "acc": self.default_acc # 加速度
                            },
                            "Move to a specified position")
        self.parser.register("moveby",self.move_by,
                            {
                            "x": 0.0, # 世界坐标系x
                            "y": 0.0, # 世界坐标系y
                            "z": 0.0, # 世界坐标系z
                            "r1": 0.0, # 末端姿态角度
                            "r2": 0.0, # 末端姿态角度
                            "r3": 0.0, # 末端姿态角度
                            "type": "MoveL", # 运动类型
                            "vel": self.default_speed, # 速度
                            "acc": self.default_acc # 加速度
                            },
                            "Move by a specified distance")
        
        self.parser.register("fromby",self.from_by,
                            {
                            "fx": 0.0, # 世界坐标系x
                            "fy": 0.0, # 世界坐标系y
                            "fz": 0.0, # 世界坐标系z
                            "f1": 0.0, # 末端姿态角度
                            "f2": 0.0, # 末端姿态角度
                            "f3": 0.0, # 末端姿态角度
                            "x": 0.0, # 世界坐标系x
                            "y": 0.0, # 世界坐标系y
                            "z": 0.0, # 世界坐标系z
                            "r1": 0.0, # 末端姿态角度
                            "r2": 0.0, # 末端姿态角度
                            "r3": 0.0, # 末端姿态角度
                            "offset": False, # 世界坐标系z
                            "type": "MoveL", # 运动类型
                            "vel": self.default_speed, # 速度
                            "acc": self.default_acc # 加速度
                            
                            },
                            "Move from pose1 to pose2")
        self.parser.register("fromto",self.from_to,
                            {
                            "fx": 0.0, # 世界坐标系x
                            "fy": 0.0, # 世界坐标系y
                            "fz": 0.0, # 世界坐标系z
                            "f1": 0.0, # 末端姿态角度
                            "f2": 0.0, # 末端姿态角度
                            "f3": 0.0, # 末端姿态角度
                            "x": 0.0, # 世界坐标系x
                            "y": 0.0, # 世界坐标系y
                            "z": 0.0, # 世界坐标系z
                            "r1": 0.0, # 末端姿态角度
                            "r2": 0.0, # 末端姿态角度
                            "r3": 0.0, # 末端姿态角度
                            "offset": False, # 世界坐标系z
                            "type": "MoveL", # 运动类型
                            "vel": self.default_speed, # 速度
                            "acc": self.default_acc # 加速度
                            },
                            "Move from pose1 to pose2")
       
        self.parser.register("reset",self.reset_all,
                            {},
                            "Reset position and gripper")
        self.parser.register("reset_pose",self.reset_pose,
                            {},
                            "Reset position")
        self.parser.register("catch",self.catch,
                            {},
                            "Catch")
        self.parser.register("put",self.put,
                            {},
                            "Put")
        self.parser.register("shut",self.shut_down,{}, "Shut down")
        self.parser.register("open",self.open_up,{}, "Open up")
        self.parser.register("cmoveto",self.move_circle_to,
                             {  
                                "x": 0.0, # 世界坐标系x
                                "y": 0.0, # 世界坐标系y
                                "z": 0.0, # 世界坐标系z
                                "r1": 0.0, # 末端姿态角度
                                "r2": 0.0, # 末端姿态角度
                                "r3": 0.0, # 末端姿态角度
                                "offset": False, # 世界坐标系z
                                "type": "MoveJ", # 运动类型
                                "vel": self.default_speed, # 速度
                                "acc": self.default_acc # 加速度 
                             }, 
                             "Move to a specified position")
        self.parser.register("init",self.arm_init,{},"Init arm")
        self.parser.register("move_close", self.MoveClose,
                         {
                             "x": 0.0,  # 世界坐标系x
                             "y": 0.0,  # 世界坐标系y
                             "z": 0.0,  # 世界坐标系z
                             "angle_a": 0.0,  # 俯仰角度
                             "angle_c": 0.0,  # 偏航角度
                             "angle_b": 0.0,  # 滚转角度
                             "s": 0.0   # 距离
                         },
                         "Move close to a specified position")
        self.parser.register("move_pose", self.MovePose,
                            {
                                "pose": "default"  # 机械臂姿态
                            },
                            "Set the pose of the arm")

        self.parser.register("fr5_init", self.fr5_init,
                            {},
                            "Initialize FR5 arm")

        self.parser.register("fr5_check_place", self.check_place_move,
                            {},
                            "Check and move FR5 arm to a safe place")

        self.parser.register("pour", self.pour,
                            {
                                "radius": 0.0,  # 容器半径
                                "height": 0.0,  # 容器高度
                                "direction": 2,  # 倾倒方向
                                "max_angle": 90.0,  # 最大倾倒角度
                                "rate_percentage": 100.0,  # 倾倒速率百分比
                                "shake": 1  # 是否抖动
                            },
                            "Pour liquid from the container")

        self.parser.register("move_to_safe_catch", self.move_to_safe_catch,
                            {
                                "aim_place": 0  # 目标安全位置索引
                            },
                            "Move to a safe place for catching")

        self.parser.register("set_nowplace", self.set_nowplace,
                            {
                                "nowplace": 0  # 当前安全位置索引
                            },
                            "Set the current safe place index")

        self.parser.register("check_place", self.check_place,
                            {},
                            "Check the current safe place index")
        self.parser.register("gripper_half", self.gripper_half, {}, "Set gripper to half open")
        self.parser.register("gripper_15", self.gripper_15, {}, "Set gripper to 15 open")
        self.parser.register("gripper_30", self.gripper_30, {}, "Set gripper to 30 open")
        self.parser.register("go_to_start_zone_0", self.Go_to_start_zone_0,
                            {
                                "v": 20.0,  # 速度
                                "open": 1   # 是否打开夹爪
                            },
                            "Reset the arm to the start zone")
        self.parser.register("reset_gripper", self.reset_gripper, {}, "reset_gripper")

    def cmd_error_handing(self):
        self.shut_down()
        pass

    def cmd_stop_handing(self):
        self.shut_down()
        pass

    def cmd_reset(self):#从error/stop恢复idle的状态
        self.open_up()
        self.facility_emergency = False
        pass

    def analyse_angle(self,x:float,y:float):
        # 计算极坐标中的 θ（与 x 轴的夹角，以弧度表示）
        theta = math.atan2(y, x)
        # 将 θ 从弧度转换为角度
        theta_degrees = math.degrees(theta)
        return theta_degrees
    
    def analyse_radians(self,x:float,y:float):
        # 计算极坐标中的 r（到原点的距离）
        r = math.sqrt(x**2 + y**2)
        return r
        
    def analyse_xy(self,r:float,theta_degrees:float):
        # 将角度从度数转换为弧度
        angle_radians = math.radians(theta_degrees)
        # 计算 x 坐标
        x = r * math.cos(angle_radians)
        # 计算 y 坐标
        y = r * math.sin(angle_radians)
        return x, y

    def move_listen(self):
        result = 0
        consecutive_non_zero_count = 0
        old_pose = [0,0,0,0,0,0]
        while True:
            ret = self.robot.GetRobotMotionDone()
            if ret[1] == 0:
                break
            else:
                consecutive_non_zero_count += 1
                if consecutive_non_zero_count == 10:
                    old_pose = self.get_pose("tool")
                    self.log.warning(f"机械臂长时间未响应")
                if consecutive_non_zero_count >= 30:
                    new_pose = self.get_pose("tool")
                    deviation = sum(abs(new - old) for new, old in zip(new_pose, old_pose))
                    if deviation <= 3.0:
                        break
                    else:
                        result = 2
                        self.log.error(f"状态超时,{old_pose},{new_pose}")
                        break
            time.sleep(0.05)

        while True and result == 0:
            if self.state == FacilityState.ERROR:
                self.log.error(f"{self.name}监听到 ERROR")
                result = 2
                break
            if self.state == FacilityState.STOP:
                self.log.error(f"{self.name}监听到 STOP")
                result = 2
                break
            ret = self.robot.GetRobotMotionDone()  # 查询机械臂运动完成状态
            if isinstance(ret, (list, tuple)):
                if ret[1] != 0:
                    consecutive_non_zero_count += 1 # 连续5次非0状态 因为开始运动时受到的第一个结果是运动完成
                    if consecutive_non_zero_count >= 5:
                        break
                else:
                    consecutive_non_zero_count = 0
            else:
                if ret != -4:
                    self.log.error(f"{self.name}状态查询错误，错误码: {ret}")
                    result = 2
                    break
            time.sleep(0.05)  # 短暂休眠，避免过于频繁的查询
        if result==2:
            self.log.error(f"机械臂运动异常")
            self.shut_down()
            self.facility_emergency = True
        else:
            self.log.info("到达")
        return result

    def move(self, new_pose: list, type="MoveL", vel_t=default_speed, acc_t=default_acc):
        if type == "MoveL":
            ret = self.robot.MoveL(new_pose, 0, 0, vel=vel_t, acc=acc_t, blendR=0)  # 笛卡尔空间直线运动
            if ret != 0:
                self.log.info(f"笛卡尔空间直线运动失败，错误码: {ret}")
                self.shut_down()
            self.move_listen()

        elif type == "MoveJ":
            inverse_kin_result = self.robot.GetInverseKin(0, new_pose, -1)
            if isinstance(inverse_kin_result, (list, tuple)) and len(inverse_kin_result) > 1:
                new_joint = list(inverse_kin_result[1])
                ret = self.robot.MoveJ(new_joint, 0, 0, new_pose, vel=vel_t, acc=acc_t, blendT=0)  # 关节空间直线运动
                if ret != 0:
                    self.log.info(f"关节空间直线运动失败，错误码: {ret}")
                    self.shut_down()

                self.move_listen()
            else:
                if inverse_kin_result == -4:
                    self.log.info("逆运动学计算失败，已到达目标位置")
                else:
                    self.log.info(f"逆运动学计算失败，错误码: {inverse_kin_result}")
                    self.shut_down()
                self.move_listen()

    def move_joint(self, new_joint: list, vel_t=default_speed, acc_t=default_acc):
        ret = self.robot.MoveJ(new_joint, 0, 0, vel=vel_t, acc=acc_t, blendT=0)  # 关节空间直线运动
        if ret != 0:
            self.log.info(f"关节空间直线运动失败，错误码: {ret}")
            self.shut_down()

        self.move_listen()


    def get_pose(self, data_type: str = None):
        if data_type == "joy":
            joint_pos = self.robot.GetActualJointPosDegree(0)
            ret = joint_pos[0]
            if ret != 0 or type(joint_pos) != tuple:
                self.log.info(f"关节角度数据获取失败，错误码: {ret}")
            else:
                return joint_pos[1]
        elif data_type == "tool":
            tool_pos = self.robot.GetActualToolFlangePose(0)
            ret = tool_pos[0]
            if ret != 0 or type(tool_pos) != tuple:
                self.log.info(f"工具位姿数据获取失败，错误码: {ret}")
            else:
                return tool_pos[1]
            
        elif data_type == "new_tool":
            tool_pos = self.robot.robot_state_pkg.tl_cur_pos
            return tool_pos

        elif data_type == None:
            joint_pos = self.robot.robot_state_pkg.jt_cur_pos
            return joint_pos

    def move_by(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,type = "MoveL",vel=default_speed,acc=default_acc):
        old_pose = self.robot.GetActualToolFlangePose(flag=0)#阻塞
        new_list = [old_pose[1][i] + val for i , val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        formatted_pose = tuple(round(x, 2) for x in new_pose)
        self.log.info(f"新位姿: {formatted_pose}")
        self.move(new_pose,type,vel,acc)


    def move_to(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,offset = False,type = "MoveL",vel=default_speed,acc=default_acc):
        new_list = [val + (self.initial_offset[i] if offset else 0) for i, val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        formatted_pose = tuple(round(x, 2) for x in new_pose)
        self.log.info(f"新位姿: {formatted_pose}")
        self.move(new_pose,type,vel,acc)

    def move_to_desc(self, desc:list, offset = False,type = "MoveL",vel=default_speed,acc=default_acc):
        new_list = [val + (self.initial_offset[i] if offset else 0) for i, val in enumerate(desc)]
        new_pose = tuple(new_list)
        formatted_pose = tuple(round(x, 2) for x in new_pose)
        self.log.info(f"新位姿: {formatted_pose}")
        self.move(new_pose,type,vel,acc)

    def move_circle(self,angle_j1:list = None):
        if angle_j1 == None:
            self.log.info("未指定角度")
        else:
            self.log.info(f"新角度: {angle_j1}")
            new_joint = self.get_pose("joy")
            new_joint[0] = angle_j1
            self.move_joint(new_joint)

    def move_circle_to(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,offset = False,type = "MoveJ",vel=default_speed,acc=default_acc):
        self.move_circle_back()
        new_j1 = self.analyse_angle(x,y) + Fr5Arm.angle_offset
        self.move_circle(new_j1)

        new_list = [val + (self.initial_offset[i] if offset else 0) for i, val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        formatted_pose = tuple(round(x, 2) for x in new_pose)
        self.log.info(f"新位姿: {formatted_pose}")
        self.move(new_pose,type,vel,acc)
        
    def move_circle_back(self):
        self.log.info("转移到安全区")
        new_pose = Fr5Arm.default_start_pose[:]
        old_pose = self.get_pose("tool")
        if self.analyse_radians(new_pose[0],new_pose[1]) < self.analyse_radians(old_pose[0],old_pose[1]):
            # 如果超出安全区，则返回安全区
            self.move_to(old_pose[0], old_pose[1], Fr5Arm.default_start_pose[2],old_pose[3],old_pose[4],old_pose[5])

            old_angle = self.get_pose("joy")
            old_j1 = old_angle[0]
            old_j1 = old_j1 - Fr5Arm.angle_offset
            
            
            new_x,new_y = self.analyse_xy(self.analyse_radians(new_pose[0],new_pose[1]),old_j1)
            self.log.info("新位置",round(new_x, 2),round(new_y, 2))
            new_pose[0] = new_x
            new_pose[1] = new_y
            new_pose[3] = old_pose[3]
            new_pose[4] = old_pose[4]
            new_pose[5] = old_pose[5]
            self.move_to(new_pose[0],new_pose[1],new_pose[2],new_pose[3],new_pose[4],new_pose[5],type="MoveJ")

    def from_by(self,fx=0, fy=0, fz=0, f1=0, f2=0, f3=0,x=0, y=0, z=0, r1=0, r2=0, r3=0,offset = False,type:str= "MoveL",vel=default_speed,acc=default_acc):
        self.move_to(fx,fy,fz,f1,f2,f3,offset=offset,type="MoveJ",vel=vel,acc=acc)
        self.move_by(x,y,z,r1,r2,r3,type=type,vel=vel,acc=acc)


    def from_to(self,fx=0, fy=0, fz=0, f1=0, f2=0, f3=0,x=0, y=0, z=0, r1=0, r2=0, r3=0,offset = False,type:str = "MoveL",vel=default_speed,acc=default_acc):
        self.move_to(fx,fy,fz,f1,f2,f3,offset=offset,type="MoveJ",vel=vel,acc=acc)
        self.move_to(x,y,z,r1,r2,r3,offset=offset,type=type,vel=vel,acc=acc)



    # def ToolPosSwitch(self,x,y,z,rx, rz, s):
    #     angle_z = self.robot.GetActualToolFlangePose()[1][5] + rz
    #     angle_x = self.robot.GetActualToolFlangePose()[1][3] + rx
    #     s_x = s*math.sin(math.radians(angle_z))*math.sin(math.radians(angle_x))
    #     s_y = s*-math.cos(math.radians(angle_z))*math.sin(math.radians(angle_x))
    #     s_z = s*math.cos(math.radians(angle_x))
    #     return (x+s_x,y+s_y,z+s_z)


    # def Pour(self,change_move,circle_s,mode):
    #     vel_t = self.default_circle_speed
    #     acc_t = self.default_circle_acc
    #     if mode == "x-":
    #         old_pose = self.robot.GetActualToolFlangePose()[1]
    #         # self.MoveTo(old_pose[0],old_pose[1],old_pose[2],90,-30,0,type="MoveL")
    #         # self.MoveBy(-change_move,0,0,0,0,0,type="MoveL")
    #         self.MoveBy((math.sqrt(3)-1)/2*circle_s,0,(math.sqrt(3)+1)/2*circle_s,0,80,0,vel=vel_t,acc=acc_t,type="MoveL")

    # def MoveTool(self,s = 0,rx = 0,rz = 0,vel=default_speed,acc=default_acc,type = "MoveL"):
    #     """
    #     以工具坐标位移一段距离。默认沿着工具y轴负方向移动。

    #     参数:
    #     s (float): 沿工具轴移动的距离。默认值为0。
    #     rx (float): 俯仰角度（度）。仰角为负
    #     rz (float): 偏航角度（度）。左偏为正
    #     vel (float): 运动速度。
    #     acc (float): 运动加速度。
    #     type (str): 运动类型。默认值为"MoveL"。

    #     返回:
    #     None
    #     """
    #     new_xyz = self.ToolPosSwitch(0,0,0,rx,rz,s)
    #     self.MoveBy(new_xyz[0],new_xyz[1],new_xyz[2],0,0,0,vel=vel,acc=acc,type=type)

    # def MovePose(self,r1=90, r2=0, r3=0):
    #     old_pose = self.robot.GetActualToolFlangePose()
    #     self.MoveTo(old_pose[1][0],old_pose[1][1],old_pose[1][2], r1, r2, r3)


    def MovePose(self,pose:str):
        r1 = 90.0
        r2 = 0.0
        r3 = 0.0
        
        if pose == 'x+':
            r3 = 0.0
            self.log.info("set x+ pose")
        elif pose == 'x-':
            r3 = 0.0
            self.log.info("set x- pose")
        elif pose == 'y+':
            r3 = 0.0
            self.log.info("set y+ pose")
        elif pose == 'y-':
            r3 = 0.0
            self.log.info("set y- pose")
        else:
            self.log.info("default pose")
                
        old_pose = self.robot.GetActualToolFlangePose()
        self.MoveTo(old_pose[1][0],old_pose[1][1],old_pose[1][2], r1, r2, r3)
        
        
    def MoveClose(self,x:float,y:float,z:float,angle_a:float,angle_c:float,angle_b:float,s:float=0):    
        s_x = -s*math.sin(math.radians(angle_a))*math.sin(math.radians(angle_b))
        s_y = -s*-math.cos(math.radians(angle_a))*math.sin(math.radians(angle_b))
        s_z = -s*math.cos(math.radians(angle_b))
        if(s == 0):
            return None
        self.MoveTo(x+s_x,y+s_y,z+s_z,angle_a,angle_c,angle_b)


    def reset_all(self):
        self.open_up()
        self.reset_pose()
        self.reset_gripper()
        

    def reset_pose(self):
        self.log.info("机械臂关节初始化")
        self.move_joint(Fr5Arm.default_start_joint)
        self.log.info("机械臂位姿初始化")
        pose = [Fr5Arm.default_start_pose[i] + self.initial_offset[i] for i in range(len(Fr5Arm.default_start_pose))]
        self.move_to(pose[0],pose[1],pose[2],pose[3],pose[4],pose[5],type="MoveJ")
        deg = self.analyse_angle(pose[0],pose[1])
        j1 = self.get_pose("joy")[0]
        Fr5Arm.angle_offset =j1 - deg
        self.log.info(f"机械臂初始角机械偏移{Fr5Arm.angle_offset}")
        self.log.info("完成")

    def reset_gripper(self):
        Info={
            '机械臂对象': self.name
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='夹爪初始化', Info=Info)
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法初始化夹爪")
        else:
            self.log.info("夹爪初始化")
            self.robot.SetGripperConfig(4, 0, 0, 1)
            time.sleep(0.5)
            self.robot.ActGripper(1, 1)
            time.sleep(3.0)
            # self.robot.MoveGripper(1, 100, 50, 10, 20000, 0, 0, 0, 0, 0)
            self.catch()
            self.put()
            # time.sleep(0.5)
            self.log.info("夹爪初始化完成")

    def catch(self):
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法使用夹爪")
        else:
            self.robot.MoveGripper(1, 0, 50, 5, 20000, 0, 0, 0, 0, 0)
            self.log.info("夹爪抓取")
            time.sleep(1.0)

    def put(self):
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法使用夹爪")
        else:
            self.robot.MoveGripper(1, 100, 50, 10, 20000, 0, 0, 0, 0, 0)
            self.log.info("夹爪放置")
            time.sleep(1.0)

    def gripper_half(self):
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法使用夹爪")
        else:
            self.robot.MoveGripper(1, 50, 50, 10, 20000, 0, 0, 0, 0, 0)
            self.log.info("夹爪半开")
            time.sleep(1.0)

    def gripper_15(self):
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法使用夹爪")
        else:
            self.robot.MoveGripper(1, 15, 50, 10, 20000, 0, 0, 0, 0, 0)
            self.log.info("夹爪开15")
            time.sleep(1.0)

    def gripper_20(self):
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法使用夹爪")
        else:
            self.robot.MoveGripper(1, 20, 50, 10, 20000, 0, 0, 0, 0, 0)
            self.log.info("夹爪开20")
            time.sleep(1.0)

    def gripper_25(self):
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法使用夹爪")
        else:
            self.robot.MoveGripper(1, 20, 50, 10, 20000, 0, 0, 0, 0, 0)
            self.log.info("夹爪开20")
            time.sleep(1.0)

    def gripper_30(self):
        if not self.can_gripper:
            self.log.warning("机械臂未使能，无法使用夹爪")
        else:
            self.robot.MoveGripper(1, 30, 50, 10, 20000, 0, 0, 0, 0, 0)
            self.log.info("夹爪开30")
            time.sleep(1.0)
        
    def shut_down(self):
        # ret = self.robot.StopMotion()
        # self.log.info(f"机械臂运动暂停{ret}")
        self.can_gripper = False
        ret = self.robot.RobotEnable(0)  # 机械臂下使能
        if ret != 0:
            self.log.warning(f"机械臂下使能失败，错误码: {ret}")
        else:
            self.log.info(f"机械臂下使能")
            self.state = ParamUtils.set_facility_state(self.state,FacilityState.STOP)

    def open_up(self):
        self.clear_error_code()
        ret = self.robot.RobotEnable(1)
        self.can_gripper = True
        if ret != 0:
            self.log.warning(f"机械臂使能失败，错误码: {ret}")
        else:
            self.log.info(f"机械臂使能")

    def clear_error_code(self):
        ret = self.robot.ResetAllError()
        if ret != 0:
            self.log.warning(f"清除错误码失败，错误码: {ret}")
        else:
            self.log.info(f"清除错误码")

    def Go_to_start_zone_0(self,v = default_speed, open = 1):
        '''
            机械臂复位
        '''
        self.log.info('机械臂复位')
        self.robot.MoveCart(self.safe_place[0], 0, 0, vel = v)
        self.now_place=0


    def find_shortest_path(self, start: int, end: int) -> list:
        distances = {node: float('infinity') for node in self.graph}
        distances[start] = 0
        previous_nodes = {node: None for node in self.graph}
        priority_queue = [(0, start)] # (distance, node)

        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            if current_distance > distances[current_node]:
                continue
            for neighbor, weight in self.graph[current_node].items():
                distance = current_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (distance, neighbor))
        path = []
        current = end
        while current is not None:
            path.insert(0, current)
            current = previous_nodes[current]

        if path[0] == start:
            return path
        else:
            return []

    def move_to_safe_catch(self, aim_place: int):
        if self.now_place == aim_place:
            return
        path = self.find_shortest_path(self.now_place, aim_place)

        if not path:
            raise HNSystemError(f"No path found from {self.now_place} to {aim_place}.")

        self.log.info(f"最短路径: {path}")

        for i, place_index in enumerate(path):
            if i == 0:
                continue

            desc_pos = self.safe_place[place_index]
            if self.name == 'fr5A':
                self.move_to_desc(desc_pos, type='MoveJ')
            elif self.name == 'fr5C':
                self.move_to_desc(desc_pos, type='MoveL', vel=self.default_fr5C_speed)
            else:
                raise HNSystemError('ERROR fr5 name!')
            self.now_place = place_index
            time.sleep(1)

    def set_nowplace(self, nowplace:int):
        self.now_place = nowplace

    def check_place(self):
        """检查机械臂当前位置是否处于预定义的安全位置
    
        通过比较机械臂当前的工具法兰位姿与预设的安全位置坐标，
        判断机械臂是否处于某个已知的安全位置点。
    
        Returns:
            int: 如果当前位置匹配某个安全位置，返回该位置的索引，如果当前位置不匹配任何预设的安全位置返回None
            
        """
        # 获取机械臂当前的工具法兰位姿 [x, y, z, rx, ry, rz]
        _, now_place = self.robot.GetActualToolFlangePose(0)
        
        # 遍历所有预设的安全位置
        for i, x in enumerate(self.safe_place):
            pd = True  # 位置匹配标志，True表示当前位置与安全位置匹配
            
            # 逐个比较位姿的6个分量：x, y, z, rx, ry, rz
            for idx, (a, b) in enumerate(zip(x, now_place)):
                # 区分位置坐标和角度坐标的处理方式
                if idx >= 3:
                    # 对于角度坐标（rx, ry, rz），考虑角度的周期性
                    # 例如：1度和359度的实际差值应该是2度，而不是358度
                    diff = min(abs(a - b), 360 - abs(a - b))
                else:
                    # 对于位置坐标（x, y, z），直接计算绝对差值
                    diff = abs(a - b)
                
                # 判断差值是否超过容差阈值（20个单位）
                if diff > 20:
                    pd = False  # 如果任何一个分量超出容差，则判定为不匹配
                    break       # 提前退出内层循环，提高效率
            
            # 如果所有6个分量都在容差范围内，则认为找到匹配的安全位置
            if pd:
                self.now_place = i  # 更新当前位置索引
                return i           # 返回匹配的安全位置索引
        
        # 如果遍历完所有安全位置都没有找到匹配的，返回None
        return None
    
    def fr5_init(self):
        self.reset_gripper()
        self.check_place_move()

    def check_place_move(self):
        """检查当前位置并移动到安全位置
    
        检查机械臂是否在安全区域，如果不在则移动到零点位置。
        用于机械臂初始化和复位操作。
        """
        self.log.info("初始化自动寻路")
        Info={
            '机械臂对象': self.name
        }
        Flowdisplay.update_process_display_dict(Process=None, Action='机械臂复位', Info=Info)
        now_place = self.check_place()
        if now_place==None:
            self.log.info("回到寻路零点")
            self.Go_to_start_zone_0()
        else:
            self.move_to_desc(self.safe_place[now_place], type='MoveJ', vel=self.default_speed)



    def pour(self, radius, height, direction=-2, max_angle=90, rate_percentage=50.0, shake=1):
        """
        机械臂倾倒动作控制
    
        通过协调末端关节旋转和笛卡尔空间补偿运动，实现液体或固体的精确倾倒。
        该方法在倾倒过程中保持出料口位置稳定，可选择性地进行抖动以确保完全倾倒。
    
        Args:
            radius (float): 容器半径 (mm) - 用于计算补偿运动轨迹
            height (float): 容器上平面到夹爪中心的高度 (mm) - 影响倾倒角度计算
            direction (int, optional): 倾倒方向和增量步长. 默认为-2
                - 负值: 逆时针倾倒
                - 正值: 顺时针倾倒
                - 数值大小: 每次伺服步进的角度增量
            max_angle (float, optional): 最大倾倒角度 (度). 默认为90度
            rate_percentage (float, optional): 运动速率百分比 (0-100). 默认为50%
            shake (int, optional): 是否启用抖动功能. 默认为1
                - 1: 启用抖动，用于固体物料的完全倾倒
                - 0: 禁用抖动
    
        Returns:
            None
        """
        # 速率参数转换
        rate_decimal = rate_percentage / 100  # 将百分比转换为小数系数
    
        # 伺服控制参数配置
        servo_cycle_time = 0.006  # 伺服循环时间 (秒)
        gain = [1.0, 1.0, 0.0, 0.0, 0.0, 0.0]  # 笛卡尔位姿增量比例系数 [X,Y,Z,RX,RY,RZ]
    
        # 获取机械臂初始状态
        tcp_pose = self.robot.GetActualTCPPose(0)  # 工具中心点位姿
        joint_pos = self.robot.GetActualJointPosDegree(0)  # 关节角度位置
    
        # 数据有效性检查与重试机制 - TCP位姿
        while type(tcp_pose) != tuple:
            tcp_pose = self.robot.GetActualToolFlangePose(0)  # 备用获取方法
            self.log.info('倾倒过程中TCP位姿数据获取失败，重试中...')
            time.sleep(0.5)
        tcp_pose = tcp_pose[1]  # 提取位姿数据 [x,y,z,rx,ry,rz]
    
        # 数据有效性检查与重试机制 - 关节位置
        while type(joint_pos) != tuple:
            joint_pos = self.robot.GetActualJointPosDegree(0)
            self.log.info('倾倒过程中关节位置数据获取失败，重试中...')
            time.sleep(0.5)
        initial_joint_pos = joint_pos[1]  # 记录初始关节位置作为倾倒角度基准

        # 几何参数计算 - 基于容器尺寸计算补偿轨迹
        slope = np.sqrt(radius**2 + height**2)  # 容器几何斜边长度
        angle_phi = np.arctan(height / radius)  # 容器几何角度
        arc_length = np.pi * slope / 180  # 单位角度对应的弧长增量
    
        # 笛卡尔空间补偿增量计算
        # 目的：在末端关节旋转时，保持出料口在空间中的位置稳定
        cartesian_increment = [
            float(2.2 * arc_length * np.sin(angle_phi) * np.sign(direction)) * rate_decimal,  # X轴补偿
            float(2.2 * arc_length * np.cos(angle_phi)) * rate_decimal,  # Y轴补偿
            0.0,  # Z轴无补偿
            0.0,  # 绕X轴旋转无补偿
            0.0,  # 绕Y轴旋转无补偿
            0.0,  # 绕Z轴旋转无补偿
        ]

        # 倾倒控制变量初始化
        joint_angle_difference = 0  # 当前倾倒角度差值
        tot = 0  # 调试计数器（未使用）
    
        # 主倾倒循环：协调关节旋转与笛卡尔补偿
        while np.abs(joint_angle_difference) < max_angle:
            # 步骤1：执行笛卡尔空间补偿运动，保持出料口位置稳定
            self.robot.ServoCart(2, cartesian_increment, gain, 0.0, 0.0, servo_cycle_time, 0.0, 0.0)
            time.sleep(servo_cycle_time * 2)  # 等待运动执行完成

            # 步骤2：获取当前关节位置并计算下一步旋转角度
            current_joint_pos = self.robot.GetActualJointPosDegree(0)
            # 数据有效性检查
            while type(current_joint_pos) != tuple:
                current_joint_pos = self.robot.GetActualJointPosDegree(0)
                self.log.info('倾倒循环中关节位置获取失败，重试中...')
                time.sleep(0.5)

            current_joint_pos = current_joint_pos[1]
        
            # 步骤3：更新末端关节角度（第6轴）
            current_joint_pos[5] = current_joint_pos[5] + direction * rate_decimal
        
            # 步骤4：执行关节空间运动
            self.robot.ServoJ(current_joint_pos, [0,0,0,0,0,0], 0.0, 0.0, servo_cycle_time, 0.0, 0.0)
            time.sleep(servo_cycle_time * 2)

            # 步骤5：更新倾倒角度差值，用于循环控制
            joint_angle_difference = current_joint_pos[5] - initial_joint_pos[5]

        # 获取倾倒完成后的最终状态
        final_joint_pos = self.robot.GetActualJointPosDegree(0)
        while type(final_joint_pos) != tuple:
            final_joint_pos = self.robot.GetActualJointPosDegree(0)
            self.log.info('倾倒完成后关节位置获取失败，重试中...')
            time.sleep(0.5)
        final_joint_pos = final_joint_pos[1]

        # 记录最终TCP位姿（用于日志记录）
        final_tcp_pose = self.robot.GetActualTCPPose(0)
        while type(final_tcp_pose) != tuple:
            final_tcp_pose = self.robot.GetActualTCPPose(0)
            self.log.info('最终TCP位姿记录失败，重试中...')
            time.sleep(0.5)
        final_tcp_pose = final_tcp_pose[1]
    
        # 抖动功能：用于固体物料的完全倾倒
        if shake == 1:
            # 抖动范围设置：围绕最终角度±6度
            max_shake_angle = final_joint_pos[5] + 6.0
            min_shake_angle = final_joint_pos[5] - 6.0
            
            shake_count = 0  # 抖动计数器
            direction = 1  # 抖动方向初始化
            
            time.sleep(3)  # 倾倒完成后等待3秒再开始抖动
            
            # 抖动循环：执行300次小幅度往复运动
            while shake_count < 300:
                # 边界检查：到达最大角度时改变方向
                if final_joint_pos[5] > max_shake_angle:
                    direction = -1
                if final_joint_pos[5] < min_shake_angle:
                    direction = 1
            
                # 更新抖动角度
                final_joint_pos[5] += direction
            
                # 执行抖动运动
                self.robot.ServoJ(final_joint_pos, [0,0,0,0,0,0], 0.0, 0.0, servo_cycle_time, 0.0, 0.0)
                time.sleep(servo_cycle_time)
                shake_count += 1

        # 记录初始TCP位姿到日志
        self.log.info(f"倾倒动作完成，初始TCP位姿: {tcp_pose}")