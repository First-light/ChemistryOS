import inspect
from typing import Dict, Any

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