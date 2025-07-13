import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from structs import FacilityState
from time import sleep

class Flowdisplay(Facility):
    type = "flowdisplay"
    
    process_display_dict = {
        'Process' : None,
        'Action' : None,
        'Info' : {}
    }

    def __init__(self, name:str = 'flowdisplay'):
        super().__init__(name, Flowdisplay.type)

    def cmd_init(self):
        pass

    def update_process_display_dict():
        pass
