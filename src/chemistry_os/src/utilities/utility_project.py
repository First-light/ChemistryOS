from dataclasses import dataclass
import sys
import os
from datetime import datetime
from typing import Literal
import typing
sys.path.append('src/chemistry_os/src')
from structs import ServerMod

@dataclass
class LogTuple:
    name: str
    log_cache: str
    log_cache_dict: dict[str, typing.Any]

class ProjectUtils:
    objects_dict = {}
    configs_dict = {}
    process_dict = {}

    @staticmethod
    def register_object(name: str, obj: typing.Any):
        """Register an object with a name."""
        ProjectUtils.objects_dict[name] = obj

    @staticmethod
    def register_process(name: str, process: typing.Any):
        """Register a process with a name."""
        ProjectUtils.process_dict[name] = process

    @staticmethod
    def register_sub_process(name: str, sub_process: typing.Any):
        """Register a subprocess with a name."""
        if 'sub_processes' not in ProjectUtils.process_dict:
            ProjectUtils.process_dict['sub_processes'] = {}
        ProjectUtils.process_dict['sub_processes'][name] = sub_process
        
    @staticmethod
    def make_json()



    