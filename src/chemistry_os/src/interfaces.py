from structs import FacilityState
import logging

class IFacility():
    """设备上下文接口"""
    name: str
    state: FacilityState
    log: logging.Logger
    facility_emergency:bool