import sys
sys.path.append('src/chemistry_os/src')
from time import sleep

class Flowdisplay():
    type = "flowdisplay"
    
    process_display_dict = {
        'Process' : None,
        'Action' : None,
        'Info' : {}
    }

    def cmd_init(self):
        pass

    def update_process_display_dict(self, Process=None, Action=None, Info=None):
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

    def data_update(self):
        pass
