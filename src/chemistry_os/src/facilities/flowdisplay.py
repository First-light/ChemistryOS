import sys
sys.path.append('src/chemistry_os/src')
from time import sleep


class Flowdisplay():
    type = "flowdisplay"
    
    process_display_dict = {
        'Process' : None,
        'Action' : None,
        'Info' : {},
        'Info_Process' : {}
    }

    def update_process_display_dict(Process=None, Action=None, Info=None, Info_Process=None):
        """
        更新流程显示字典
        :param Process: 流程名称
        :param Action: 当前动作
        :param Info: 附加信息
        """
        if Process is not None:
            Flowdisplay.process_display_dict['Process'] = Process
        if Action is not None:
            Flowdisplay.process_display_dict['Action'] = Action
        if Info is not None:
            Flowdisplay.process_display_dict['Info'] = Info
        if Info_Process is not None:
            Flowdisplay.process_display_dict['Info_Process'] = Info_Process

    def data_update():
        pass
