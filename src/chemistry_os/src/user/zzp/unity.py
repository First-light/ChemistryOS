class DeviceType():
    MECHANICAL_ARM = 1
    SMALL_MECHANICAL_ARM = 2
    FEEDING_PUMP = 3
    RINSING_PUMP = 4
    WATER_BATH = 5
    SOLID_FEEDING = 6
    INSTRUMENT_POSITION = 7

class Gripper_status():
    OPEN=0
    CLOSED=1

class Running_status():
    ON=0
    OFF=1

class Weighing_status():
    SYS_STATUS_IDLE = 0
    SYS_STATUS_WAKE = 1
    SYS_STATUS_BUSY = 2

class Tube_position():
    VERTICAL = 0
    HORIZONTAL = 1

# 示例数据
mechanical_arm_status = {
    "type": DeviceType.MECHANICAL_ARM,
    "joint_angles": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "gripper_status": Gripper_status.OPEN
}

small_mechanical_arm_status = {
    "type": DeviceType.SMALL_MECHANICAL_ARM,
    "joint_angles": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "gripper_status": Gripper_status.CLOSED
}

feeding_peristaltic_pump_status = {
    "type": DeviceType.FEEDING_PUMP,
    "status": Running_status.ON,
    "speed": 100,
    "runtime": 300,
    "remaining_time": 600,
    "fed_amount": 500,
    "total_amount": 1000,
    "remaining_amount": 500
}

rinsing_peristaltic_pump_status = {
    "type": DeviceType.RINSING_PUMP,
    "status": Running_status.OFF,
    "speed": 0,
    "runtime": 0,
    "remaining_time": 0
}

water_bath_status = {
    "type": DeviceType.WATER_BATH,
    "power_status": Running_status.ON,
    "current_temperature": 37.5,
    "set_temperature": 37.0,
    "stirring_status": Running_status.ON,
    "cooling_status": Running_status.OFF,
    "heating_status": Running_status.ON,
}

solid_feeding_status = {
    "type": DeviceType.SOLID_FEEDING,
    "gripper_status": Gripper_status.OPEN,
    "tube_position": Tube_position.VERTICAL,
    "weighing_status": Running_status.OFF,
    "target_weight": 1000.0,
    "current_weight": 500.0
}

instrument_position_status = {
    "type": DeviceType.INSTRUMENT_POSITION,
    "instrument":
    [
        {
            "instrument_type": "graduated cylinder",
            "initial_position": [0,0,0]
        },
        {
            "instrument_type": "beaker",
            "initial_position": [0,0,0]
        }
    ]
}

if __name__ == '__main__':
    print(mechanical_arm_status)
