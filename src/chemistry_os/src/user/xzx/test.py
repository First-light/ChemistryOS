import sys
sys.path.append('src/chemistry_os/src')
from parser import CommandParser 
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_fr3arm import Fr3Arm

if __name__ == '__main__':
    fr5A = Fr5Arm("fr5A","192.168.58.2")
    fr5_C = Fr3Arm("fr3C","192.168.58.3")
    # #测试类模版
    # test = facility_temp("temp",1,2)
    # test.message()
    # facility_temp.type = "temp4"
    # test2 = facility_temp("test2",2,3)
    # test2.message()
    # test3 = facility_temp("test3",2,3)
    # test3.message()

    # #指令输入与格式错误提示
    # test = facility_temp("test1",1,2)
    # test.parser.cmd("list")
    # test.parser.cmd("message")
    # test.parser.cmd("output param1=3 param2=4")
    # test.parser.cmd("output param3=3 param2=4")
    # test.parser.cmd("output param3 param2=4")
    # test.parser.cmd("output param1= param2=4")

    #全局指令系统测试
    # test = FacilityTemp("temp",1,2)
    main_parser = CommandParser()
    # main_parser.parse("temp output param1=3 param2=4")
    # main_parser.parse("temp")
    # main_parser.parse("te")

    exit()