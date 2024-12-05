import sys
sys.path.append('src/chemistry_os/src')
from facilities.class_fr5arm import fr5robot
from facilities.class_template import facility_temp

if __name__ == '__main__':
    # fr5A = fr5robot("fr5A","192.168.58.6")

    # #测试类模版
    # test = facility_temp("test1",1,2)
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

    
    exit()