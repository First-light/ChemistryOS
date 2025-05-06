task_flow = [
    {
        "flow_id": 1,
        'flow_name':'合成A',
        'steps':[
            {
                "step_id": 1,
                "step_name":'固体进料',
                "parameters": {
                    "source": 'space_A',
                    "quality": 0.5
                }
            },
            {
                "step_id": 2,
                "step_name":'倾倒',
                "parameters": {
                    "source": 'space_A',
                    "dict": 'space_B'
                }
            }
        ]
    },
    {
        "flow_id": 2,
        'flow_name':'合成B',
        'steps':[
            {
                "step_id": 1,
                "step_name":'固体进料',
                "parameters": {
                    "source": 'space_A',
                    "quality": 0.5
                }
            },
            {
                "step_id": 2,
                "step_name":'倾倒',
                "parameters": {
                    "source": 'space_A',
                    "dict": 'space_B'
                }
            }
        ]
    }
]

class TaskType():
    # 流程状态，表示当前更新的是某个流程
    FLOW_STATUS = 0
    # 步骤状态，表示当前更新的是流程中的某个步骤
    STEP_STATUS = 1
    # 动作状态，表示当前更新的是步骤中的某个具体动作
    ACTION_STATUS = 2
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

solid_feeding_status = {
    "type": DeviceType.SOLID_FEEDING,
    "gripper_status": Gripper_status.OPEN,
    "tube_position": Tube_position.VERTICAL,
    "weighing_status": Running_status.OFF,
    "target_weight": 1000.0,
    "current_weight": 500.0
}

{
    "TaskType": 0,
    "flow_id": 1,
}
{
    "TaskType": 1,
    "step_id": 1,
    "step_name":'固体进料',
    "step_type":1,
}
{
    "TaskType": 2,
    "action_id": 1,
    "action_name":'进料',
    "action_type":1,
    "parameters": 
    {
        "source": 'space_A',
        "dict": 'space_B'
    }
}