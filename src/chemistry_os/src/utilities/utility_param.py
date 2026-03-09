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
    CompoundC_solid_add = 1.0                    # 化合物C的添加量
    HCl_volume_add = 22.73*CompoundC_solid_add    # 浓盐酸
    KMnO4_volume_add = 45.45*CompoundC_solid_add # 高锰酸钾添加量 
    H2O2_volume_add = 11.36*CompoundC_solid_add   # 双氧水添加量
    N2H4_volume_add = 1.2*CompoundC_solid_add   # 肼添加量

    CH3CN_volume_add = 60.0*CompoundC_solid_add # 乙腈添加量
    HCl_volume_wash = 15.0*CompoundC_solid_add   # 稀盐酸冲洗量
    water_volume_wash = 30.0*CompoundC_solid_add # 冰水冲洗量

    HCl_rpm = 100
    KMnO4_rpm = 15
    H2O2_rpm = 30
    N2H4_rpm = 5

    liquid_volume_pump = 200 # ml
    liquid_2_volume_pump = HCl_volume_wash + water_volume_wash 

    HCl_temp = -5           #浓盐酸滴加温度
    KMnO4_temp = -5         #高锰酸钾滴加温度
    H2O2_temp = 25          #双氧水滴加温度
    N2H4_temp = 25          #水合肼滴加温度

    reaction_time_0 = 900   # 浓盐酸后反应时间
    reaction_time_mix = 300   # 搅拌时间
    reaction_temp_0 = -5
    reaction_time_1 = 7200  # 高锰酸钾后反应时间
    reaction_temp_1 = 25    # 高锰酸钾后反应温度
    reaction_time_2 = 1200  # 双氧水后反应时间
    reaction_temp_2 = 25    # 双氧水后反应温度
    reaction_time_3 = 7200 # 水合肼后反应时间
    reaction_temp_3 = 25    # 水合肼后反应温度
    project_name  = "flow_project"
    init_name = "flow_reset"
    



class ParamUtils:

    param_dict:Dict[str, Any] = {}

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
    def param_dict_update():
        ParamUtils.param_dict.update(ParamUtils.get_param_dict())

    @staticmethod
    def get_param_dict() -> Dict[str, Any]:
        """
        获取ParamTuple类中所有参数的字典
        :return: 包含所有参数名和值的字典
        """
        param_dict = {}
        
        # 获取ParamTuple类的所有属性
        for attr_name in dir(ParamTuple):
            if not attr_name.startswith('_'):  # 过滤以下划线开头的内部属性
                attr_value = getattr(ParamTuple, attr_name)
                # 只包含非方法的属性（即数据属性）
                if not callable(attr_value):
                    param_dict[attr_name] = attr_value
        # print(param_dict)
        return param_dict

    @staticmethod 
    def set_facility_state(old_state:FacilityState,state:FacilityState) -> FacilityState:
        result:FacilityState
        if state.value < old_state.value:
            # LogUtils.log.warning(f"设备状态不能降级: {facility.name} {facility_old_state} -> {state}")
            result = old_state
        else:
            result = state
        return result

