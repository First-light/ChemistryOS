import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
import os
import json

class Project(Facility):

    def __init__(self,name:str,file:str):
        super().__init__(name)
        self.load(file)

    def cmd_init(self):
        self.parser.register("load", self.load, {"file": ''}, "load file")
        pass

    def load(self, file: str):
        if file == '':
            self.cmd_print_head
            print("Please input the file name.")
            return
        
        json_file_path = os.path.join(os.path.dirname(__file__), 'json/', file + ".json")
        self.cmd_print_head
        print("path: ",json_file_path)
        if not os.path.isfile(json_file_path):
            self.cmd_print_head
            print(f"File {file}.json does not exist.")
        else:
            self.file = json_file_path
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cmd_print_head
                    print("JSON file content: ", data)
                    # 你可以在这里对解析后的 JSON 数据进行进一步处理
                    self.data = data
            except json.JSONDecodeError as e:
                self.cmd_print_head
                print(f"Error decoding JSON file: {e}")



        

