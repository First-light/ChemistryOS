from dataclasses import dataclass
from logging import Logger
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

class LogUtils:
    log_cache = []  # 公用日志缓存区
    log_cache_dict = {
        "data": None,
        "server_mod": int(ServerMod.SKIP.value),
    }  # 公用日志缓存区字典
    log:Logger = None #公用logger


    