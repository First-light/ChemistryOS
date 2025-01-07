## 简介

HN软件控制配置与流程标准化分析设计实现，使用`python`编写

## 快速使用

为了确保正常工作，需要以下版本或工具：

+ ubuntu 20.04/22.04
+ python 3.10(.4)


## 文件结构
```shell
├── CMakeLists.txt
└── chemistry_os/
    ├── package.xml
    ├── CMakeLists.txt
    ├── src/
    │   ├── usage.mk
    │   ├── main.py
    │   ├── Robot.so
    │   ├── parser.py
    │   ├── test.py
    │   └── facility.py
    └── facilities/ 
        ├── facility_fr5arm.py
        ├── facility_system.py
        ├── facility_project.py
        ├── facility_temp.py
        ├── pkgcmd.py
        └── json/
            ├── arm.json
            ├── lines.json
            ├── test.json
            └── sub.json
```
## 说明

新的代码结构设计，是站在软件工程设计上思考。

### 设备参数
默认参数与指令定义在类中，用户参数定义在json文件中，可通过输入指令修改，不需要重新编译。
### 单一步骤
使用字符串指令解析的方式查找方法，再进行调用并注入参数，提供不需再编译的动作实现方法；用户步骤可通过json导入，格式化为字符串指令。
### 设备通信
每个流程都有通信接收器与执行器，执行器使用传统的阻塞式通信方式，监听设备，接收器用于控制执行器运行，监听程序指令，设备监听不占用主程序的正常运作。
### 运行过程
使用多线结构，包含一条控制主线和用户接口线，用户接口线负责循环绘制用户UI以及输出信息，接收用户控制命令，并转移给控制主线的缓存，控制主线负责解析并执行缓存中的指令，可以直接控制设备，执行函数，也可以创建流程支线，读取json文件然后运行流程，支线与控制主线互不冲突，允许重复执行某一流程，暂停流程并执行其他流程。
