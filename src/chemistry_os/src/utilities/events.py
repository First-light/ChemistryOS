import time
import threading
import sys
import select

sys.path.append('src/chemistry_os/src')
from utilities.utility_log import LogUtils
from facilities.flowdisplay import Flowdisplay
from facilities.facility_parser import CommandParser

def event_countdown(seconds, name:str = '', rpm:float = 0, volume:float = 0, directon:bool = 1):
    start_time = time.time()
    end_time = start_time + seconds
    
    # 用于控制是否停止的标志
    stop_flag = threading.Event()
    
    def input_thread():
        while not stop_flag.is_set():
            try:
                user_input = CommandParser.wait_input("parser", "输入 'q' 跳过倒计时...")
                if user_input.lower() == 'q':
                    stop_flag.set()
                    break
            except:
                break
    
    # 启动输入线程
    input_t = threading.Thread(target=input_thread, daemon=True)
    input_t.start()
    
    while time.time() < end_time:
        # 检查是否收到停止信号
        if stop_flag.is_set():
            print("\n手动停止计时")
            break
            
        # 计算剩余时间
        now = time.time()
        remaining_time = end_time - now
        
        if remaining_time <= 0:
            break
            
        finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        
        # 使用 \r 回到行首覆盖输出，end='' 避免换行
        print(f"\r剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}", end='', flush=True)
        
        if directon==0:
            Info = {
                '进料液体': name,
                '进料转速': str(rpm) + ' 转/min',
                '剩余时间' : str(int(remaining_time)) + ' s',
                '预计结束时间' : finish_time
            }
            Flowdisplay.update_process_display_dict(Process=None, Action='蠕动泵反转', Info=Info)
        elif name != '':
            elapsed_time = now - start_time
            current_volume = volume * elapsed_time / seconds
            Info = {
                '进料液体': name,
                '进料转速': str(rpm) + ' 转/min',
                '已加料体积': f"{current_volume:.2f} ml",
                '目标体积': str(volume) + ' ml',
                '剩余时间' : str(int(remaining_time)) + ' s',
                '预计结束时间' : finish_time
            }
            Flowdisplay.update_process_display_dict(Process=None, Action='液料滴加', Info=Info)
        
        # 短暂等待后继续监控
        time.sleep(1)
    
    stop_flag.set()  # 确保输入线程结束
    
    if time.time() >= end_time:
        LogUtils.log.info("时间到")
    
    total_time = time.time() - start_time
    LogUtils.log.info(f"倒计时结束，总耗时: {int(total_time)} 秒")