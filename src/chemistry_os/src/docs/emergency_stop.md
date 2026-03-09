# 机械臂急停检测机制文档

## 概述

本项目实现了一个三层急停检测机制，确保当机械臂检测到急停时，整个化学实验流程能够安全、协调地停止。

## 检测机制

### 1. 硬件层检测（状态轮询）

**位置**：`facilities/facility_fr5arm.py:76-86`

```python
def emergency_detect_func(self):
    # 检测机械臂急停标志位，检测到后将机械臂软件标签位设置为ERROR
    while self.emergency_detect:
        if self.robot.robot_state_pkg.EmergencyStop and self.state != FacilityState.ERROR:
            self.log.error(f"{self.name}机械臂检测到急停，设置状态为ERROR")
            self.state = ParamUtils.set_facility_state(self.state, FacilityState.ERROR)
        time.sleep(0.03)
```

**工作原理**：
1. **启动检测线程**：通过 `start_emergency_detect()` 方法（第66-75行）启动独立线程
2. **轮询检测**：每 30 毫秒轮询一次 `self.robot.robot_state_pkg.EmergencyStop` 状态
3. **SDK API**：使用 Fairino SDK 的 `EmergencyStop` 属性读取物理急停按钮的状态
4. **状态转换**：检测到急停时，将设备状态切换到 `ERROR`

### 2. 软件层检测（装饰器拦截）

**位置**：`utilities/utility_emergency.py`

```python
class EmergencyUtils:
    if_emergency = False  # 全局急停状态

def emergency_check(available_emergency=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if EmergencyUtils.if_emergency and not available_emergency:
                raise EmergencyException("Function execution aborted due to emergency state.")
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**工作原理**：
1. **全局状态检查**：`EmergencyUtils.if_emergency` 作为全局急停开关
2. **函数级拦截**：装饰器在函数执行前检查全局急停状态
3. **可控例外**：`available_emergency` 参数允许特定函数在急停状态下执行

### 3. 设备层检测（状态传播）

**位置**：`facilities/facility.py:38`

每个 Facility 子类都有 `facility_emergency` 布尔属性，用于设备级别的紧急状态控制。

## 触发其他设备急停的逻辑

### 设备级紧急状态传播

1. **机械臂异常触发**（`facility_fr5arm.py:399`）：
   ```python
   self.facility_emergency = True
   ```

2. **其他设备检查**（例如 `facility_sdk.py:580,638`）：
   ```python
   if self.facility_emergency:
       # 拒绝执行新命令
   ```

3. **项目流程控制**（`facility_project.py:55`）：
   ```python
   if not self.facility_emergency:
       # 执行步骤
   ```

### 命令处理器级别的状态同步

**位置**：`pkgcmd.py:125-130`

```python
if self.obj_state == FacilityState.BUSY and self.facility.facility_emergency is not True:
    self.obj_state = FacilityState.IDLE
else:
    self.obj_log.error(f"设备运行时状态异常：{self.obj_state} 紧急：{self.facility.facility_emergency}")
    if self.facility.facility_emergency:
        self.obj_state = ParamUtils.set_facility_state(self.facility.state, FacilityState.ERROR)
```

### 设备停止和错误处理

1. **命令级别停止**：
   - `cmd_error_handing()` 和 `cmd_stop_handing()` 方法设置 `facility_emergency = True`
   - Filter 设备会停止所有泵和阀门控制

2. **系统级锁定**（`pkgcmd.py:147`）：
   ```python
   self.facility.facility_emergency = True
   ```

## 恢复机制

通过 `cmd_reset()` 方法，各设备可实现从紧急状态恢复：

```python
def cmd_reset(self):
    self.facility_emergency = False
    pass
```

## 相关文件

| 文件 | 说明 |
|------|------|
| `facilities/facility_fr5arm.py` | 机械臂急停检测实现 |
| `utilities/utility_emergency.py` | 全局急停状态管理和装饰器 |
| `facilities/facility.py` | 设备基础类，定义 `facility_emergency` 属性 |
| `facilities/facility_sdk.py` | SDK 设备的紧急状态检查 |
| `facilities/facility_project.py` | 项目流程的紧急状态检查 |
| `pkgcmd.py` | 命令处理器的状态同步 |

## 工作流程总结

```
机械臂物理急停按钮
    ↓ (SDK API轮询, 30ms/次)
robot_state_pkg.EmergencyStop
    ↓ (检测线程)
机械臂 state = ERROR
    ↓
facility_emergency = True
    ↓ (状态传播)
其他设备检测到紧急状态
    ↓
拒绝执行新命令 / 停止运行中命令
```

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                     硬件层                                │
│  物理急停按钮 ──[SDK]──> EmergencyStop 状态              │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼ (30ms轮询)
┌─────────────────────────────────────────────────────────┐
│                   设备层 (机械臂)                         │
│  emergency_detect_func() → state = ERROR               │
│  facility_emergency = True                              │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼ (状态传播)
┌─────────────────────────────────────────────────────────┐
│               设备层 (其他设备)                           │
│  - facility_sdk.py: 检查 facility_emergency            │
│  - facility_project.py: 检查 facility_emergency        │
│  - facility_filter.py: 检查 facility_emergency         │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  软件层 (装饰器)                          │
│  @emergency_check 装饰器 → EmergencyException          │
│  EmergencyUtils.if_emergency 全局开关                   │
└─────────────────────────────────────────────────────────┘
```
