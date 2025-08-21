from dataclasses import dataclass
import inspect
import sys
from typing import Dict, Any
sys.path.append('src/chemistry_os/src')
from structs import FacilityState
from interfaces import IFacility
from utilities.utility_log import LogUtils

@dataclass
class ParamTuple:
    CompoundC_solid_add = 0.5 # 化合物C的添加量
    HCL_volume_add = 26.8*CompoundC_solid_add # 浓盐酸
    KMnO4_volume_add = 53.52*CompoundC_solid_add # 高锰酸钾添加量 
    H2O2_volume_add = 20.0*CompoundC_solid_add # 双氧水添加量
    HCL_L_volume_add = 80.0*CompoundC_solid_add
    CH3CN_volume_add = 20.0 # 乙腈添加量
    N2H4_volume_add = 0.4854 # 肼添加量
    HCl_rpm = 100
    KMnO4_rpm = 15
    H2O2_rpm = 30
    CH3CN_rpm = 30
    N2H4_rpm = 30
    tmp_0 = 0
    tmp_25 = 25
    reaction_time_1 = 7200
    reaction_time_2 = 1200
    reaction_time_3 = 14400
    project_name  = "flow_project"
    init_name = "flow_init"
    



class ParamUtils:
    
    @staticmethod
    def get_init_params(instance) -> Dict[str, Any]:
        """
        静态方法：自动获取初始化参数
        
        :param instance: 类实例
        :return: 参数字典
        """
        try:
            # 获取 __init__ 方法的参数名
            sig = inspect.signature(instance.__class__.__init__)
            param_names = [name for name in sig.parameters.keys() if name != 'self']
            
            # 获取调用者的栈帧（即 __init__ 方法的栈帧）
            frame = inspect.currentframe()
            caller_frame = frame.f_back  # 调用这个静态方法的栈帧
            caller_locals = caller_frame.f_locals  # 调用者的局部变量
            
            # 创建参数字典
            init_dict = {}
            for param_name in param_names:
                if param_name in caller_locals:
                    init_dict[param_name] = caller_locals[param_name]
            
            return init_dict
            
        except Exception as e:
            print(f"参数提取失败: {e}")
            return {}
        finally:
            # 清理栈帧引用，避免内存泄漏
            if 'frame' in locals():
                del frame

    @staticmethod  
    def set_param_value(param_name: str, value: Any):
        """
        修改ParamTuple类中的参数值
        :param param_name: 参数名字符串
        :param value: 新的参数值
        """
        if hasattr(ParamTuple, param_name):
            setattr(ParamTuple, param_name, value)
            LogUtils.log.info(f"{param_name} : {value}")
        else:
            LogUtils.log.info(f"ParamTuple没有参数: {param_name}")

    @staticmethod 
    def set_facility_state(old_state:FacilityState,state:FacilityState) -> FacilityState:
        result:FacilityState
        if state.value < old_state.value:
            # LogUtils.log.warning(f"设备状态不能降级: {facility.name} {facility_old_state} -> {state}")
            result = old_state
        else:
            result = state
        return result

