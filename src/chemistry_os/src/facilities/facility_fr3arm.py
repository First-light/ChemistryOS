import sys
sys.path.append('src/chemistry_os/src')
import time
import Robot # type: ignore # 根目录在src下
import math
import numpy as np
from facility import Facility
from structs import FacilityState
from facilities.facility_fr5arm import Fr5Arm

class Fr3Arm(Fr5Arm):
    type = "fr3arm"
    default_speed = 20.0
    default_acc = 10.0
    default_circle_speed = 5.0
    default_circle_acc = 40.0
    default_start_pose = [-340.0,-38.0,345,90,-45,-90]
    default_start_joint = [-14.725,-93.459,86.909,6.594,77.775,45.0]
    angle_offset = 45.0
    saved_pose = [0,0,0,0,0,0]

    safe_place=[
        [215.0,-225.0,160.0,90.0,-45.0,45.0], #bath
        [215.0,-225.0,398.0,90.0,-45.0,45.0], #catch
        [55.0,-225.0,398.0,90.0,-45.0,-45.0]
    ]

    def __init__(self, name: str, ip: str):
        self.robot = Robot.RPC(ip)
        self.name = name
        super().__init__(name, Fr3Arm.type)
        self.type = Fr3Arm.type
        
    def reset_all(self):
        self.open_up()
        self.reset_pose()
        self.reset_gripper()
        

    def reset_pose(self):
        print("机械臂关节初始化")
        self.move_joint(Fr3Arm.default_start_joint)
        print("机械臂位姿初始化")
        pose = [Fr3Arm.default_start_pose[i] + self.initial_offset[i] for i in range(len(Fr3Arm.default_start_pose))]
        self.move_to(pose[0],pose[1],pose[2],pose[3],pose[4],pose[5],type="MoveJ")
        deg = self.analyse_angle(pose[0],pose[1])
        j1 = self.get_pose("joy")[0]
        Fr3Arm.angle_offset =j1 - deg
        print(f"机械臂初始角机械偏移{Fr3Arm.angle_offset}")
        print("完成")

    def reset_gripper(self):
        print("夹爪初始化")
        self.catch()   
        self.put()
        print("完成")

    def catch(self):
        self.robot.SetToolDO(0,1,0,0)
        self.robot.SetToolDO(1,0,0,0)
        time.sleep(1)


    def put(self):
        self.robot.SetToolDO(0,0,0,0)
        self.robot.SetToolDO(1,1,0,0)
        time.sleep(1)

    def clear_error_code(self):
        ret = self.robot.ResetAllError()
        self.message_head()
        print(f"清除错误码:{ret}")

    def delay(self,sec:float):
        print("delay ",sec)
        time.sleep(sec)

    def move_to_catch(self):
        self.move_to_desc([215.0,-225.0,398.0,90.0,-45.0,45.0],vel=5)
        time.sleep(1)

    def move_to_bath(self):
        self.move_to_desc([215.0,-225.0,160.0,90.0,-45.0,45.0],vel=5)
        time.sleep(1)

    def move_to_pour(self):
        self.move_to_desc([215.0,-225.0,160.0,90.0,-45.0,45.0],vel=5)
        time.sleep(1)

    def fr3_init(self):
        self.put()
        now_place = self.check_place()
        if now_place==None:
            self.move_to_catch()
        else:
            self.move_to_desc(self.safe_place[now_place], type='MoveJ', vel=15)

if __name__ == '__main__':
    exit()