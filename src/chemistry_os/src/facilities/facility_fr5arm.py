import json
import sys

sys.path.append('src/chemistry_os/src')
from user.zzp.simple_client import TCPClient
from user.zzp.unity import DeviceType,Gripper_status,Running_status,Weighing_status,Tube_position
import time
import Robot # type: ignore # 根目录在src下
import math
import numpy as np
from facility import Facility
from structs import FacilityState

class Fr5Arm(Facility):
    type = "fr5arm"
    default_speed = 20.0
    default_acc = 10.0
    default_circle_speed = 5.0
    default_circle_acc = 40.0
    default_start_pose = [0,-250,400,90,0,0]
    default_start_joint = [-45.548,-48.178,-126.989,-184.834,-43.048,0]
    angle_offset = 45.0
    saved_pose = [0,0,0,0,0,0]

    safe_place=[
        [-250.0, -250.0, 350.0, 90.0, 0.0, -90.0],
        [0.0, -250.0, 350.0, 90.0, 0.0, 0.0],
        [200.0, -150.0, 350.0, 90.0, 0.0, 90.0],
        [100.0, 200.0, 400.0, 90.0, 0.0, 180.0]
    ]
    
    position_file_path = "src/chemistry_os/src/facilities/location/fr5.json"

    def __init__(self, name: str, ip: str):
        super().__init__(name, Fr5Arm.type)
        self.robot = Robot.RPC(ip)
        self.arm_init()

    def arm_init(self):
        ret, version = self.robot.GetSDKVersion()  # 查询SDK版本号
        if ret == 0:
            self.log.info(f"FR5机械臂SDK版本号为: {', '.join(version)}")
        else:
            self.log.info(f"FR5机械臂查询失败，错误码: {ret}")
        try:
            temp_ip = self.robot.GetControllerIP()  # 查询控制器IP
            if isinstance(temp_ip, tuple) and len(temp_ip) == 2:
                temp, ip_check = temp_ip
                if temp == 0:
                    self.log.info("FR5控制器IP查询成功")
                else:
                    raise RuntimeError(f"FR5机械臂IP检查错误，错误码: {temp}")
            else:
                temp = temp_ip
                raise RuntimeError(f"FR5机械臂IP检查错误，错误码: {temp}")
        except RuntimeError as e:
            self.log.info(f"运行时错误: {e}")
            self.state[0] = FacilityState.ERROR
            self.log.info("机械臂初始化失败")
            return

        self.log.info(f"FR5控制器IP为: {ip_check}")
        self.initial_offset = [0, 0, 0, 0, 0, 0]  # 机械臂初始位置与世界坐标系原点的偏差
        self.open_up()

        with open(self.position_file_path, 'r') as file:
            self.obj_status = json.load(file)
        self.obj_status_init()


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
                            "x": 0, # 世界坐标系x
                            "y": 0, # 世界坐标系y
                            "z": 0, # 世界坐标系z
                            "r1": 0, # 末端姿态角度
                            "r2": 0, # 末端姿态角度
                            "r3": 0, # 末端姿态角度
                            "type": "MoveL", # 运动类型
                            "vel": self.default_speed, # 速度
                            "acc": self.default_acc # 加速度
                            },
                            "Move to a specified position")
        self.parser.register("moveby",self.move_by,
                            {
                            "x": 0, # 世界坐标系x
                            "y": 0, # 世界坐标系y
                            "z": 0, # 世界坐标系z
                            "r1": 0, # 末端姿态角度
                            "r2": 0, # 末端姿态角度
                            "r3": 0, # 末端姿态角度
                            "type": "MoveL", # 运动类型
                            "vel": self.default_speed, # 速度
                            "acc": self.default_acc # 加速度
                            },
                            "Move by a specified distance")
        
        self.parser.register("fromby",self.from_by,
                            {
                            "fx": 0, # 世界坐标系x
                            "fy": 0, # 世界坐标系y
                            "fz": 0, # 世界坐标系z
                            "f1": 0, # 末端姿态角度
                            "f2": 0, # 末端姿态角度
                            "f3": 0, # 末端姿态角度
                            "x": 0, # 世界坐标系x
                            "y": 0, # 世界坐标系y
                            "z": 0, # 世界坐标系z
                            "r1": 0, # 末端姿态角度
                            "r2": 0, # 末端姿态角度
                            "r3": 0, # 末端姿态角度
                            "offset": False, # 世界坐标系z
                            "type": "MoveL", # 运动类型
                            "vel": self.default_speed, # 速度
                            "acc": self.default_acc # 加速度
                            
                            },
                            "Move from pose1 to pose2")
        self.parser.register("fromto",self.from_to,
                            {
                            "fx": 0, # 世界坐标系x
                            "fy": 0, # 世界坐标系y
                            "fz": 0, # 世界坐标系z
                            "f1": 0, # 末端姿态角度
                            "f2": 0, # 末端姿态角度
                            "f3": 0, # 末端姿态角度
                            "x": 0, # 世界坐标系x
                            "y": 0, # 世界坐标系y
                            "z": 0, # 世界坐标系z
                            "r1": 0, # 末端姿态角度
                            "r2": 0, # 末端姿态角度
                            "r3": 0, # 末端姿态角度
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
                                "x": 0, # 世界坐标系x
                                "y": 0, # 世界坐标系y
                                "z": 0, # 世界坐标系z
                                "r1": 0, # 末端姿态角度
                                "r2": 0, # 末端姿态角度
                                "r3": 0, # 末端姿态角度
                                "offset": False, # 世界坐标系z
                                "type": "MoveJ", # 运动类型
                                "vel": self.default_speed, # 速度
                                "acc": self.default_acc # 加速度 
                             }, 
                             "Move to a specified position")
        self.parser.register("init",self.arm_init,{},"Init arm")

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
        res = 0
        while True:
            if self.state[0] == FacilityState.ERROR:
                self.shut_down()
                res = 2
                break
            if self.state[0] == FacilityState.STOP:
                self.shut_down()
                res = 2
                break

            ret = self.robot.GetRobotMotionDone()  # 查询机器人运动完成状态
            if isinstance(ret, (list, tuple)):
                if ret[1] != 0:
                    break
            else:
                if ret != -4:
                    self.log.info(f"状态查询错误，错误码: {ret}")
                    self.shut_down()
                    res = 2
                    break
            time.sleep(0.005)
        return res

    def move(self, new_pose: list, type="MoveL", vel_t=default_speed, acc_t=default_acc):
        if type == "MoveL":
            ret = self.robot.MoveL(new_pose, 0, 0, vel=vel_t, acc=acc_t, blendR=0.0)  # 笛卡尔空间直线运动
            if ret != 0:
                self.log.info(f"笛卡尔空间直线运动失败，错误码: {ret}")
                self.shut_down()
            self.move_listen()

        elif type == "MoveJ":
            inverse_kin_result = self.robot.GetInverseKin(0, new_pose, -1)
            if isinstance(inverse_kin_result, (list, tuple)) and len(inverse_kin_result) > 1:
                new_joint = list(inverse_kin_result[1])
                ret = self.robot.MoveJ(new_joint, 0, 0, new_pose, vel=vel_t, acc=acc_t, blendT=0.0)  # 关节空间直线运动
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

    def move_joint(self, new_joint: list, vel_t=default_speed, acc_t=default_acc):
        ret = self.robot.MoveJ(new_joint, 0, 0, vel=vel_t, acc=acc_t, blendT=0.0)  # 关节空间直线运动
        if ret != 0:
            self.log.info(f"关节空间直线运动失败，错误码: {ret}")
            self.shut_down()

        self.move_listen()


    def get_pose(self, data_type: str):
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

    def move_by(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,type = "MoveL",vel=default_speed,acc=default_acc):
        old_pose = self.robot.GetActualToolFlangePose()
        new_list = [old_pose[1][i] + val for i , val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        self.log.info(f"新位姿: {new_pose}")
        self.move(new_pose,type,vel,acc)
        self.log.info("到达")
        mechanical_arm_status = {
            "type": DeviceType.MECHANICAL_ARM,
            "joint_angles": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "gripper_status": Gripper_status.OPEN
        }

    def move_to(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,offset = False,type = "MoveL",vel=default_speed,acc=default_acc):
        new_list = [val + (self.initial_offset[i] if offset else 0) for i, val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        self.log.info(f"新位姿: {new_pose}")
        self.move(new_pose,type,vel,acc)
        self.log.info("到达")

    def move_to_desc(self, desc:list, offset = False,type = "MoveL",vel=default_speed,acc=default_acc):
        new_list = [val + (self.initial_offset[i] if offset else 0) for i, val in enumerate(desc)]
        new_pose = tuple(new_list)
        self.log.info(f"新位姿: {new_pose}")
        self.move(new_pose,type,vel,acc)
        self.log.info("到达")

    def move_circle(self,angle_j1:list = None):
        if angle_j1 == None:
            self.log.info("未指定角度")
        else:
            self.log.info(f"新角度: {angle_j1}")
            new_joint = self.get_pose("joy")
            new_joint[0] = angle_j1
            self.move_joint(new_joint)
            self.log.info("到达")

    def move_circle_to(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,offset = False,type = "MoveJ",vel=default_speed,acc=default_acc):
        self.move_circle_back()
        new_j1 = self.analyse_angle(x,y) + Fr5Arm.angle_offset
        self.move_circle(new_j1)

        # 先降下高度
        # old_pose = self.get_pose("tool")
        # self.move_to(old_pose[0],old_pose[1],z,old_pose[3],old_pose[4],old_pose[5])

        new_list = [val + (self.initial_offset[i] if offset else 0) for i, val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        self.log.info("新位姿",new_pose)
        self.move(new_pose,type,vel,acc)
        self.log.info("到达")
        
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
            self.log.info("新位置",new_x,new_y)
            new_pose[0] = new_x
            new_pose[1] = new_y
            new_pose[3] = old_pose[3]
            new_pose[4] = old_pose[4]
            new_pose[5] = old_pose[5]
            self.move_to(new_pose[0],new_pose[1],new_pose[2],new_pose[3],new_pose[4],new_pose[5],type="MoveJ")
            self.log.info("到达")

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
            print("set x+ pose")
        elif pose == 'x-':
            r3 = 0.0
            print("set x- pose")
        elif pose == 'y+':
            r3 = 0.0
            print("set y+ pose")
        elif pose == 'y-':
            r3 = 0.0
            print("set y- pose")
        else:
            print("default pose")
                
        old_pose = self.robot.GetActualToolFlangePose()
        self.MoveTo(old_pose[1][0],old_pose[1][1],old_pose[1][2], r1, r2, r3)
        
        
    def MoveClose(self,x:float,y:float,z:float,angle_a:float,angle_c:float,angle_b:float,s:float=0):    
        s_x = -s*math.sin(math.radians(angle_a))*math.sin(math.radians(angle_b))
        s_y = -s*-math.cos(math.radians(angle_a))*math.sin(math.radians(angle_b))
        s_z = -s*math.cos(math.radians(angle_b))
        if(s == 0):
            return None
        self.MoveTo(x+s_x,y+s_y,z+s_z,angle_a,angle_c,angle_b)
        

    # def pourwater(self,pour_position,pour_direction,sel_num,clockwise = False):
    #     '''
    #     指定位置倾倒指定仪器
    #     预期效果： 机械臂运动到指定位置————机械臂倾倒仪器————机械臂等待倾倒完毕————机械臂抖动————机械臂回到一个中立位置
    #     pour_position: 目标绝对xyz坐标
    #     pour_direction: ym——y轴负方向  xm——x负方向
    #     sel_num:倾倒的对象 1---试管 2---烧杯 3---量筒 4---反应瓶
    #     '''
    #     print("目标物体绝对xyz坐标:",pour_position)
    #     rxryrz = []
    #     if pour_direction == "yn":
    #         print("倾倒方向是：y轴负方向")
    #         # 数据处理y
    #         pour_position[1] = pour_position[1] + 150.0
    #         pour_position[0] = pour_position[0]
    #         if clockwise:
    #             rxryrz = [90.0, -30.0, 0.0]
    #         else:
    #             rxryrz = [90.0, 30.0, 0.0]
    #     elif pour_direction == "xn":
    #         print("倾倒方向是：x轴负方向")
    #         # 数据处理x
    #         pour_position[0] = pour_position[0] + 150.0
    #         rxryrz = [90.0, 0.0, -90.0]
    #     elif pour_direction == "xp":
    #         print("倾倒方向是：x轴正方向")
    #         # 数据处理x
    #         pour_position[0] = pour_position[0] - 150
    #         rxryrz = [90.0, 0.0, 90.0]
    #     else:
    #         print("------error!-------")
    #         exit()
    #     # 合法检测
    #     if len(pour_position) != 3:
    #         print("xyz坐标错误")
    #         exit()
    #     else:
    #         print("----------------------")   
        
    #     if int(sel_num) == 1:
    #         print("倾倒的对象：试管")
    #         pour_position[2] += 10.0
    #         bias = 20
    #         height = 10
    #     elif int(sel_num) == 2:
    #         print("倾倒的对象：烧杯")
    #         pour_position[2] += 10.0
    #         bias = 37
    #         height = 35
    #     elif int(sel_num) == 3:
    #         print("倾倒的对象：量筒")
    #         pour_position[2] += 10.0
    #         bias = 20
    #         height = 50     
    #     else:
    #         print("--------Wrong sel index!---------")
    #         exit()

    #     pour_position += rxryrz
    #     print('==========================',pour_position)


    #     if pour_direction == "yn":
    #         # y方向留bias距离 z方向留height距离
    #         position1 = pour_position
    #         if clockwise:
    #             position1[0] = position1[0] - bias
    #         else:
    #             position1[0] = position1[0] + bias
    #         position1[2] = position1[2] + height * math.cos(math.fabs(rxryrz[1]) * math.pi / 180)
    #         self.robot.MoveCart(position1,0,0)
    #         time.sleep(2)
    #     elif pour_direction == "xn":
    #         # x方向留bias距离 z方向留height距离
    #         position1 = pour_position
    #         position1[0] = position1[0] + bias
    #         position1[2] = position1[2] + height
    #         self.robot.MoveCart(position1,0,0)
    #         time.sleep(2)
    #     elif pour_direction == "xp":
    #         # x方向留bias距离 z方向留height距离
    #         position1 = pour_position
    #         position1[0] = position1[0] - bias
    #         position1[2] = position1[2] + height
    #         self.robot.MoveCart(position1,0,0)
    #         time.sleep(2)
    #     max_angle = 100
    #     pre_angle = math.fabs(90 - math.fabs(rxryrz[1]))

    #     if clockwise == False:
    #         bias = -bias
            
    #     self.pour(math.fabs(bias), height, float(2 * numpy.sign(bias)), max_angle, 100)
    #     # time.sleep(1)
    #     # self.Go_to_start_zone(open=False)
    #     print("动作完成")


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
        self.log.info("夹爪初始化")
        self.robot.SetGripperConfig(4, 0, 0, 1)
        time.sleep(0.5)
        self.robot.ActGripper(1, 1)
        time.sleep(1.5)
        self.robot.MoveGripper(1, 100, 50, 10, 10000, 1)
        time.sleep(0.5)
        self.log.info("夹爪初始化完成")
        
    # def Release_DiGuan(self):
    #     self.robot.MoveGripper(1, 20, 20, 10, 10000, 1)
    #     time.sleep(2.0)
    # def Push_DiGuan(self):
    #     self.robot.MoveGripper(1, 0, 20, 10, 10000, 1)
    #     time.sleep(2.0)

    def catch(self):
        self.robot.MoveGripper(1, 0, 50, 5, 10000, 1)
        time.sleep(2.0)

    def put(self):
        self.robot.MoveGripper(1, 100, 50, 10, 10000, 1)   
        time.sleep(2.0)

    def gripper_half(self):
        self.robot.MoveGripper(1, 50, 50, 10, 10000, 1)
        time.sleep(2.0)

    def gripper_15(self):
        self.robot.MoveGripper(1, 15, 50, 10, 10000, 1)
        time.sleep(2.0)
    
    def gripper_30(self):
        self.robot.MoveGripper(1, 30, 50, 10, 10000, 1)
        time.sleep(2.0)
        
    def shut_down(self):
        ret = self.robot.RobotEnable(0)  # 机器人下使能
        self.log.info(f"机器人下使能，返回值: {ret}")
        if self.state[0] == FacilityState.IDLE or self.state[0] == FacilityState.BUSY:
            self.state[0] = FacilityState.STOP

    def open_up(self):
        self.clear_error_code()
        ret = self.robot.RobotEnable(1)
        self.log.info(f"机器人使能，返回值: {ret}")
        self.state[0] = FacilityState.IDLE

    def clear_error_code(self):
        ret = self.robot.ResetAllError()
        self.log.info(f"清除错误码，返回值: {ret}")

    def delay(self,sec:float):
        print("delay ",sec)
        time.sleep(sec)

    def Go_to_start_zone_0(self,v = 10.0, open = 1):
        '''
            机械臂复位
        '''
        print('机械臂复位')
        self.robot.MoveCart(self.safe_place[0], 0, 0, vel = v)
        self.now_place=0

    def move_to_safe_catch(self, aim_place:int):
        if aim_place>self.now_place:
            for i in range(self.now_place+1, aim_place+1):
                desc_pos = self.safe_place[i]
                print(i)
                print(desc_pos)
                self.move_to_desc(desc_pos, type='MoveJ', vel=15)
                time.sleep(1)
        else:
            for i in range(self.now_place-1, aim_place-1, -1):
                desc_pos = self.safe_place[i]
                print(i)
                print(desc_pos)
                self.move_to_desc(desc_pos, type='MoveJ', vel=15)
                time.sleep(1)
        self.now_place = aim_place

    def set_nowplace(self, nowplace:int):
        self.now_place = nowplace

    def check_place(self):
        _, now_place = self.robot.GetActualToolFlangePose(0)
        for i, x in enumerate(self.safe_place):
            pd = True
            for idx, (a, b) in enumerate(zip(x, now_place)):
                if idx >= 3:
                    diff = min(abs(a - b), 360 - abs(a - b))
                else:
                    diff = abs(a - b)
                if diff > 5:
                    pd = False
                    break
            if pd:
                self.now_place = i
                return i
        return None
    
    def fr5_init(self):
        self.reset_gripper()
        now_place = self.check_place()
        if now_place==None:
            self.Go_to_start_zone_0()
        else:
            self.move_to_desc(self.safe_place[now_place], type='MoveJ', vel=15)


    # radius=参数为容器半径mm，height=容器上平面离夹爪中心高度mm，direction=角度方向与增量，max_angle=倾倒最大角度，rate_percentage=运动速率的百分比
    def pour(self, radius, height, direction=-2, max_angle=90, rate_percentage=100.0, shake=1):
        # 将速率百分比转换为小数形式
        rate_decimal = rate_percentage / 100
        
        # 伺服运动参数预置
        servo_cycle_time = 0.006
        gain = [1.0, 1.0, 0.0, 0.0, 0.0, 0.0]  # 位姿增量比例系数
        
        # 获取初始工具坐标系位姿和关节位置
        tcp_pose = self.robot.GetActualTCPPose(0)
        joint_pos = self.robot.GetActualJointPosDegree(0)
        
        # 确保获取到有效的 TCP 位姿数据
        while type(tcp_pose) != tuple:
            tcp_pose = self.robot.GetActualToolFlangePose(0)
            print('Failed to get initial TCP pose from SDK during pouring')
            time.sleep(0.5)
        tcp_pose = tcp_pose[1]
        
        # 确保获取到有效的关节位置数据
        while type(joint_pos) != tuple:
            joint_pos = self.robot.GetActualJointPosDegree(0)
            print('Failed to get initial joint position from SDK during pouring')
            time.sleep(0.5)
        initial_joint_pos = joint_pos[1]

        # 计算旋转参数
        slope = np.sqrt(radius**2 + height**2)
        angle_phi = np.arctan(height / radius)
        arc_length = np.pi * slope / 180  # 弧长增量
        
        # 计算工具坐标系下的笛卡尔增量
        cartesian_increment = [
            float(2.2 * arc_length * np.sin(angle_phi) * np.sign(direction)) * rate_decimal,
            float(2.2 * arc_length * np.cos(angle_phi)) * rate_decimal,
            0.0,
            0.0,
            0.0,
            0.0,
        ]

        joint_angle_difference = 0  # 确保进入倾倒循环
        
        # 倾倒循环：在末端关节伺服旋转时，执行空间伺服运动以确保出料口位置稳定
        while np.abs(joint_angle_difference) < max_angle:
            self.robot.ServoCart(2, cartesian_increment, gain, 0.0, 0.0, servo_cycle_time, 0.0, 0.0)  # 工具笛卡尔坐标增量移动

            current_joint_pos = self.robot.GetActualJointPosDegree(0)
            # 确保获取到有效的关节位置数据
            while type(current_joint_pos) != tuple:
                current_joint_pos = self.robot.GetActualJointPosDegree(0)
                print('Failed to get current joint position from SDK during pouring')
                time.sleep(0.5)
            current_joint_pos = current_joint_pos[1]
            current_joint_pos[5] = current_joint_pos[5] + direction * rate_decimal

            self.robot.ServoJ(current_joint_pos, 0.0, 0.0, servo_cycle_time, 0.0, 0.0)  # 关节角增量移动

            time.sleep(servo_cycle_time)

            # 更新关节角度差值
            joint_angle_difference = current_joint_pos[5] - initial_joint_pos[5]

        # 获取最终关节位置
        final_joint_pos = self.robot.GetActualJointPosDegree(0)
        while type(final_joint_pos) != tuple:
            final_joint_pos = self.robot.GetActualJointPosDegree(0)
            print('Failed to get final joint position from SDK after pouring')
            time.sleep(0.5)
        final_joint_pos = final_joint_pos[1]

        # 记录最终位置
        final_tcp_pose = self.robot.GetActualTCPPose(0)
        while type(final_tcp_pose) != tuple:
            final_tcp_pose = self.robot.GetActualTCPPose(0)
            print('Failed to get final TCP pose record')
            time.sleep(0.5)
        final_tcp_pose = final_tcp_pose[1]
        
        # 设置最大和最小角度以进行固体抖动
        max_shake_angle = final_joint_pos[5] + 6.0
        min_shake_angle = final_joint_pos[5] - 6.0
        
        shake_count = 0
        if shake == 1:
            time.sleep(3)
            while shake_count < 300:
                self.robot.ServoJ(final_joint_pos, 0.0, 0.0, servo_cycle_time, 0.0, 0.0)
                if final_joint_pos[5] > max_shake_angle:
                    direction = -1
                if final_joint_pos[5] < min_shake_angle:
                    direction = 1
                final_joint_pos[5] += direction

                time.sleep(servo_cycle_time)
                shake_count += 1

        print(tcp_pose)

        # # 回归初始位置
        # self.move_to_desc(tcp_pose, vel=10)
        # time.sleep(1)
            

if __name__ == '__main__':
    exit()