from dataclasses import dataclass


@dataclass
class EmergencyUtils:
    if_emergency: bool = False


class EmergencyException(Exception):
    pass


def emergency_check(available_emergency=None):
    """
    装饰器：根据急停状态和 available_emergency 参数决定是否执行函数
    :param available_emergency: 是否允许在急停状态下执行，默认为 False
    """
    # 如果装饰器没有传入参数，则 available_emergency 为 None，此时需要处理为默认值
    if available_emergency is None:
        available_emergency = False

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 检查急停状态
            if EmergencyUtils.if_emergency and not available_emergency:
                raise EmergencyException("Function execution aborted due to emergency state.")

            # 正常执行被修饰的函数
            return func(*args, **kwargs)

        return wrapper

    return decorator

if __name__ == "__main__":
    # 测试代码
    @emergency_check(available_emergency=False)
    def test_function():
        print("Function executed successfully.")

    @emergency_check(available_emergency=True)
    def test_function_emergency_allowed():
        print("Function executed successfully even in emergency state.")

    try:
        EmergencyUtils.if_emergency = True  # 模拟急停状态
        test_function_emergency_allowed()
        test_function()
    except EmergencyException as e:
        print(e)  # 输出: Function execution aborted due to emergency state.

    EmergencyUtils.if_emergency = False  # 恢复正常状态
    test_function_emergency_allowed()
    test_function()  # 输出: Function executed successfully.