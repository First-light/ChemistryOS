import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_parser import CommandParser 
import Robot  # type: ignore # 根目录在src下

if __name__ == '__main__':
  
    # 全局指令系统测试
    robot = Robot.RPC('192.168.58.2')
    ret, version = robot.GetSDKVersion()  # 查询SDK版本号
    if ret == 0:
        print(f"FR5机械臂SDK版本号为: {', '.join(version)}")
    else:
        print(f"FR5机械臂查询失败，错误码: {ret}")
    print("program_state:", robot.robot_state_pkg.program_state)
    print("robot_state:", robot.robot_state_pkg.robot_state)
    print("main_code:", robot.robot_state_pkg.main_code)
    print("sub_code:", robot.robot_state_pkg.sub_code)
    print("robot_mode:", robot.robot_state_pkg.robot_mode)
    
    # jt_cur_pos
    for i in range(6):
        print(f"jt_cur_pos{i}:", robot.robot_state_pkg.jt_cur_pos[i])

    # tl_cur_pos
    for i in range(6):
        print(f"tl_cur_pos{i}:", robot.robot_state_pkg.tl_cur_pos[i])

    # flange_cur_pos
    for i in range(6):
        print(f"flange_cur_pos{i}:", robot.robot_state_pkg.flange_cur_pos[i])

    # actual_qd
    for i in range(6):
        print(f"actual_qd{i}:", robot.robot_state_pkg.actual_qd[i])

    # actual_qdd
    for i in range(6):
        print(f"actual_qdd{i}:", robot.robot_state_pkg.actual_qdd[i])

    # target_TCP_CmpSpeed
    for i in range(2):
        print(f"target_TCP_CmpSpeed{i}:", robot.robot_state_pkg.target_TCP_CmpSpeed[i])

    # target_TCP_Speed
    for i in range(6):
        print(f"target_TCP_Speed{i}:", robot.robot_state_pkg.target_TCP_Speed[i])

    # actual_TCP_CmpSpeed
    for i in range(2):
        print(f"actual_TCP_CmpSpeed{i}:", robot.robot_state_pkg.actual_TCP_CmpSpeed[i])

    # actual_TCP_Speed
    for i in range(6):
        print(f"actual_TCP_Speed{i}:", robot.robot_state_pkg.actual_TCP_Speed[i])

    # jt_cur_tor
    for i in range(6):
        print(f"jt_cur_tor{i}:", robot.robot_state_pkg.jt_cur_tor[i])

    # 单值属性
    print("tool:", robot.robot_state_pkg.tool)
    print("user:", robot.robot_state_pkg.user)
    print("cl_dgt_output_h:", robot.robot_state_pkg.cl_dgt_output_h)
    print("cl_dgt_output_l:", robot.robot_state_pkg.cl_dgt_output_l)
    print("tl_dgt_output_l:", robot.robot_state_pkg.tl_dgt_output_l)
    print("cl_dgt_input_h:", robot.robot_state_pkg.cl_dgt_input_h)
    print("cl_dgt_input_l:", robot.robot_state_pkg.cl_dgt_input_l)
    print("tl_dgt_input_l:", robot.robot_state_pkg.tl_dgt_input_l)

    # cl_analog_input
    for i in range(2):
        print(f"cl_analog_input{i}:", robot.robot_state_pkg.cl_analog_input[i])

    print("tl_anglog_input:", robot.robot_state_pkg.tl_anglog_input)

    # ft_sensor_raw_data
    for i in range(6):
        print(f"ft_sensor_raw_data{i}:", robot.robot_state_pkg.ft_sensor_raw_data[i])

    # ft_sensor_data
    for i in range(6):
        print(f"ft_sensor_data{i}:", robot.robot_state_pkg.ft_sensor_data[i])

    print("ft_sensor_active:", robot.robot_state_pkg.ft_sensor_active)
    print("EmergencyStop:", robot.robot_state_pkg.EmergencyStop)
    print("motion_done:", robot.robot_state_pkg.motion_done)
    print("gripper_motiondone:", robot.robot_state_pkg.gripper_motiondone)
    print("mc_queue_len:", robot.robot_state_pkg.mc_queue_len)
    print("collisionState:", robot.robot_state_pkg.collisionState)
    print("trajectory_pnum:", robot.robot_state_pkg.trajectory_pnum)
    print("safety_stop0_state:", robot.robot_state_pkg.safety_stop0_state)
    print("safety_stop1_state:", robot.robot_state_pkg.safety_stop1_state)
    print("gripper_fault_id:", robot.robot_state_pkg.gripper_fault_id)
    print("gripper_fault:", robot.robot_state_pkg.gripper_fault)
    print("gripper_active:", robot.robot_state_pkg.gripper_active)
    print("gripper_position:", robot.robot_state_pkg.gripper_position)
    print("gripper_speed:", robot.robot_state_pkg.gripper_speed)
    print("gripper_current:", robot.robot_state_pkg.gripper_current)
    print("gripper_tmp:", robot.robot_state_pkg.gripper_tmp)
    print("gripper_voltage:", robot.robot_state_pkg.gripper_voltage)

    # auxState
    print("auxState.servoId:", robot.robot_state_pkg.auxState.servoId)
    print("auxState.servoErrCode:", robot.robot_state_pkg.auxState.servoErrCode)
    print("auxState.servoState:", robot.robot_state_pkg.auxState.servoState)
    print("auxState.servoPos:", robot.robot_state_pkg.auxState.servoPos)
    print("auxState.servoVel:", robot.robot_state_pkg.auxState.servoVel)
    print("auxState.servoTorque:", robot.robot_state_pkg.auxState.servoTorque)

    exit()