import sys
sys.path.append('src/chemistry_os/src/facilities')
import time
import Robot # type: ignore # 根目录在src下
import math
import numpy
from class_template import facility
from class_template import facility_state

class fr5robot(facility):
    default_speed = 50.0
    default_acc = 60.0
    default_circle_speed = 5.0
    default_circle_acc = 40.0

    def __init__(self,name:str,ip:str):   
        super().__init__(name)
        self.robot = Robot.RPC(ip)
        self.initial_offset = [0,0,0,0,0,0] # 机械臂初始位置与世界坐标系原点的偏差
        self.message_start()
        ret,version  = self.robot.GetSDKVersion()    #查询SDK版本号
        if ret == 0:
            print("FR5机械臂SDK版本号为", version )
        else:
            print("FR5机械臂查询失败，错误码为",ret)
            sys.exit(1)
            
        temp_ip = self.robot.GetControllerIP()  # 查询控制器IP
        if isinstance(temp_ip, tuple) and len(temp_ip) == 2:
            temp, ip_check = temp_ip
            if temp == 0:
                print("FR5控制器IP为", ip_check)
            else:
                print("FR5机械臂IP检查错误,错误码为", temp)
                sys.exit(1)
        else:
            temp = temp_ip
            print("FR5机械臂IP检查错误,错误码为", temp)
            sys.exit(1)

        ret = self.robot.RobotEnable(1)   #机器人上使能
        print(name,"","FR5机器人上使能", ret)    
        self.message_end()
        self.type = facility_state.IDLE

    def offset_init(self,x,y,z,r1,r2,r3):
        self.initial_offset = [x,y,z,r1,r2,r3]

    def cmd_init(self):
        self.parser.register(
            "moveto",
            self.MoveTo,
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
            "Move to a specified position"
        )
        self.parser.register(
            "moveby",
            self.MoveBy,
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
            "Move by a specified distance"
        )

    # def ShowData(self):
    #     self.message_start()
    #     print("工具位姿",self.robot.GetActualTCPPose())
    #     print("关节角度",self.robot.GetActualJointPosDegree())
    #     print("末端法兰位姿",self.robot.GetActualToolFlangePose())
    #     self.message_end()
        
    def Move(self,new_pose,type = "MoveL",vel_t=default_speed,acc_t=default_acc):
        if type == "MoveL":
            ret = self.robot.MoveL(new_pose, 0, 0, vel=vel_t, acc =acc_t,blendR = 0.0)  # 笛卡尔空间直线运动
            if ret != 0:
                self.message_head()
                print("笛卡尔空间直线运动:错误码", ret)
                self.ShutDown()
                sys.exit(1)
            while(self.robot.GetRobotMotionDone()[1] == 0):
                time.sleep(0.2)

        elif type == "MoveJ":
            inverse_kin_result = self.robot.GetInverseKin(0, new_pose, -1)
            if isinstance(inverse_kin_result, (list, tuple)) and len(inverse_kin_result) > 1:
                new_joint = list(inverse_kin_result[1])
                ret = self.robot.MoveJ(new_joint, 0, 0, new_pose, vel=vel_t, acc=acc_t, blendT=0.0)  # 关节空间直线运动
                if ret != 0:
                    self.message_head()
                    print("关节空间直线运动:错误码", ret)
                    self.ShutDown()
                    sys.exit(1)
                while self.robot.GetRobotMotionDone()[1] == 0:
                    time.sleep(0.2)
            else:
                self.message_head()
                print("逆运动学计算失败，错误码： ",inverse_kin_result)
                self.ShutDown()
                sys.exit(1)


    def MoveBy(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,type = "MoveL",vel=default_speed,acc=default_acc):
        old_pose = self.robot.GetActualToolFlangePose()
        new_list = [old_pose[1][i] + val for i , val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        self.message_head()
        print("新位姿",new_pose)
        self.Move(new_pose,type,vel,acc)
        self.message_head()
        print("到达")


    def MoveTo(self,x=0, y=0, z=0, r1=0, r2=0, r3=0,offset = False,type = "MoveL",vel=default_speed,acc=default_acc):
        new_list = [val + (self.initial_offset[i] if offset else 0) for i, val in enumerate([x, y, z, r1, r2, r3])]
        new_pose = tuple(new_list)
        self.message_head()
        print("新位姿",new_pose)
        self.Move(new_pose,type,vel,acc)
        self.message_head()
        print("到达")
        

        
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


    # def MovePose(self,pose):
    #     r1 = 90.0
    #     r2 = 0.0
    #     r3 = 0.0
    #     self.message_head()
    #     if pose == 'x+':
    #         r3 = 0.0
    #         print("set x+ pose")
    #     elif pose == 'x-':
    #         r3 = 0.0
    #         print("set x- pose")
    #     elif pose == 'y+':
    #         r3 = 0.0
    #         print("set y+ pose")
    #     elif pose == 'y-':
    #         r3 = 0.0
    #         print("set y- pose")
    #     else:
    #         print("default pose")
                
    #     old_pose = self.robot.GetActualToolFlangePose()
    #     self.MoveTo(old_pose[1][0],old_pose[1][1],old_pose[1][2], r1, r2, r3)
        
        
    # def MoveClose(self,x,y,z,angle_a,angle_c,angle_b,s=0):    
    #     s_x = -s*math.sin(math.radians(angle_a))*math.sin(math.radians(angle_b))
    #     s_y = -s*-math.cos(math.radians(angle_a))*math.sin(math.radians(angle_b))
    #     s_z = -s*math.cos(math.radians(angle_b))
    #     if(s == 0):
    #         return None
    #     self.MoveTo(x+s_x,y+s_y,z+s_z,angle_a,angle_c,angle_b)
        
        

        
    # def pour(self, r, h, i=-2, max_angel=90, rate = 100.0, v = 70.0, upright = 1, shake = 1):
    #     rate /= 100
    #     types = {
    #         "100ml": {"diameter": 10, "height": 20},
    #         "200ml": {"diameter": 15, "height": 25},
    #         "250ml": {"diameter": 12, "height": 22},
    #     }
    #     # 伺服运动参数预置
    #     t=0.002
    #     eP0 = [0.000, 0.000, 0.000, 0.000]
    #     dP0 = [1.000, 1.000, 1.000, 1.000, 1.000, 1.000]
    #     gain = [1.0, 1.0, 0.0, 0.0, 0.0, 0.0]  # 位姿增量比例系数，仅在增量运动下生效，范围[0~1]
        
    #     P1 = self.robot.GetActualTCPPose(0)
    #     J1 = self.robot.GetActualJointPosDegree(0)
    #     while( type(P1) != tuple):
    #         P1 = self.robot.GetActualToolFlangePose(0)
    #         print('when executing pouring,failed to get P1 from sdk')
    #         time.sleep(0.5)
    #     P1 = P1[1]
    #     while( type(J1) != tuple):
    #         J1 = self.robot.GetActualJointPosDegree(0)
    #         print('when executing pouring,failed to get J1 from sdk')
    #         time.sleep(0.5)
    #     J1 = J1[1]

    #     # 计算旋转参数
    #     R = math.sqrt(r**2 + h**2)
    #     phi = numpy.arctan(h / r)
    #     l = math.pi * R / 180  # 弧长（x理论增量）
    #     # 工具坐标笛卡尔增量
    #     n_pos = [
    #         float(2.2 * l * math.sin(phi) * numpy.sign(i)) * rate,
    #         float(2.2 * l * math.cos(phi)) * rate,
    #         0.0,
    #         0.0,
    #         0.0,
    #         0.0,
    #     ]

    #     joint_pos_difference = 0  # 确保进入倾倒循环
        
    #     # 在末端关节伺服旋转时，执行空间伺服运动以确保仪器出料口位置稳定
    #     # 可通过修改单步时延t的大小来调整旋转速度
    #     while math.fabs(joint_pos_difference) < max_angel:
    #         self.robot.ServoCart(2, n_pos, gain, 0.0, 0.0, t, 0.0, 0.0)  # 工具笛卡尔坐标增量移动

    #         joint_pos = self.robot.GetActualJointPosDegree(0)
    #         while( type(joint_pos) != tuple):
    #             joint_pos = self.robot.GetActualJointPosDegree(0)
    #             print('when executing pouring,failed to get end_height_from_sdk2')
    #             time.sleep(0.5)
    #         joint_pos = joint_pos[1]
    #         joint_pos[5] = joint_pos[5] + i * rate

    #         self.robot.ServoJ(joint_pos, 0.0, 0.0, t, 0.0, 0.0)  # 关节角增量移动

    #         time.sleep(t)

    #         # 更新差值
    #         joint_pos_difference = joint_pos[5] - J1[5]

    #     joint_pos = self.robot.GetActualJointPosDegree(0)
    #     while( type(joint_pos) != tuple):
    #         joint_pos = self.robot.GetActualJointPosDegree(0)
    #         print('when executing pouring,failed to get end_height_from_sdk2')
    #         time.sleep(0.5)
    #     joint_pos = joint_pos[1]
    #     pos_record = self.robot.GetActualTCPPose(0)
    #     while( type(pos_record) != tuple):
    #         pos_record = self.robot.GetActualTCPPose(0)
    #         print('when executing pouring,failed to get pos record')
    #         time.sleep(0.5)
    #     pos_record = pos_record[1]
    #     max_angel = joint_pos[5] + 6.0
    #     min_angel = joint_pos[5] - 6.0
    #     shakes = 0
    #     if shake == 1:
    #         while shakes < 200:
    #             self.robot.ServoJ(joint_pos, 0.0, 0.0, t, 0.0, 0.0)
    #             if joint_pos[5] > max_angel:
    #                 i = -1
    #             if joint_pos[5] < min_angel:
    #                 i = 1
    #             joint_pos[5] += i

    #             time.sleep(0.002)
    #             shakes += 1
    #         self.robot.MoveCart(pos_record, 0, 0, 0.0, 0.0, v, -1.0, -1)
            
    #     # 回到倾倒起点，有些场景下可能需要，暂时保留
    #     # self.MoveL(0.0, 0.0, (300 - self.robot.GetActualTCPPose(0)[3]), 50.0)
    #     # time.sleep(0.5)
        
    #     # 是否需要上抬以规避倾倒仪器回归水平位时的碰撞
    #     if upright == 0:
    #         return
    #     else:
    #         P1 = self.robot.GetActualTCPPose(0)[1]
    #         P1[2] += 60.0
    #         if math.fabs(P1[5]) > 80.0 and math.fabs(P1[5]) < 170.0:
    #             P1 = P1[0:3]
    #             P1 += [90.0, 0.0, -90.0]
    #         else:
    #             P1 = P1[0:3]
    #             P1 += [90.0, 0.0, 0.0]
    #         self.robot.MoveCart(P1, 0, 0, 0.0, 0.0, v, -1.0, -1)

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


    def Reset_Pose(self):
        self.message_head()
        print("机械臂位置初始化")
        # new_joint = [-47.157,-48.142,-126.999,-184.859,-47.157, 0.0]
        # p1 = self.robot.GetForwardKin(new_joint)[1]
        # ret = self.robot.MoveJ(new_joint, 0, 0, p1, vel=self.default_speed, acc=self.default_acc, blendT=0.0)  # 关节空间直线运动
        # if ret != 0:
        #     self.message_head()
        #     print("关节空间直线运动:错误码", ret)
        #     self.ShutDown()
        #     sys.exit(1)
        # while self.robot.GetRobotMotionDone()[1] == 0:
        #     time.sleep(0.1)
        self.MoveTo(0.0, -250.0, 400.0, 90.0, 0.0, 0.0,type="MoveJ")
        self.message_head()
        print("完成")


    def Reset_Gripper(self):
        self.message_head()
        print("夹爪初始化")
        self.robot.SetGripperConfig(4, 0, 0, 1)
        time.sleep(0.5)
        self.robot.ActGripper(1, 1)
        time.sleep(2)
        self.robot.MoveGripper(1, 100, 50, 10, 10000, 1)
        time.sleep(0.5)
        self.message_head()
        print("完成")
        
    # def Release_DiGuan(self):
    #     self.robot.MoveGripper(1, 20, 20, 10, 10000, 1)
    #     time.sleep(2.0)
    # def Push_DiGuan(self):
    #     self.robot.MoveGripper(1, 0, 20, 10, 10000, 1)
    #     time.sleep(2.0)

    # def Catch(self):
    #     self.robot.MoveGripper(1, 0, 50, 5, 10000, 1)
    #     time.sleep(2.0)
    # def Put(self):
    #     self.robot.MoveGripper(1, 100, 50, 10, 10000, 1)   
    #     time.sleep(2.0)
        
    def ShutDown(self):
        ret = self.robot.RobotEnable(0)   #机器人下使能
        self.message_head()
        print("机器人下使能", ret)

    def message_start(self):
        print("\n<",self.name,">:")
    def message_head(self):
        print("<",self.name,">: ",end="")
    def message_end(self):
        print("\n")

    # def Catch_to_start(self,x,y,z):
    #     self.MoveTo(x,y+80,z+150,90,0,0)
    #     self.MoveTo(x,y+80,z,90,0,0)
    #     self.MoveTool(80.0)
    #     self.Catch()
    #     self.MoveBy(z=200.0)
    #     self.Reset_Pose()

    # def Put_to_ground(self,x,y,z):
    #     self.MoveTo(x,y,z+150,90,0,0)
    #     self.MoveTo(x,y,z,90,0,0)
    #     self.Put()
    #     self.MoveBy(y=100.0)
    #     self.MoveBy(z=200.0)
    #     self.Reset_Pose()

    # def Shake(self,num):
    #     self.MoveBy(x=-20,r2=30,vel=100,acc=100)
    #     for i in range(num):
    #         self.MoveBy(x=40,r2=-60,vel=100,acc=100)
    #         self.MoveBy(x=-40,r2=60,vel=100,acc=100)
    #     self.MoveBy(x=20,r2=-30,vel=100,acc=100)


if __name__ == '__main__':
    exit()