import time
import threading
import sys
import select

def event_countdown(seconds):
    # 用于控制是否继续计时的事件
    stop_event = threading.Event()
    countdown_finished_event = threading.Event()

    def countdown(seconds):
        start_time = time.time()  # 获取当前时间
        end_time = start_time + seconds  # 计算结束时间

        while seconds > 0 and not stop_event.is_set():  # 计时中如果stop_event触发就停止
            # 计算剩余时间
            now = time.time()
            remaining_time = end_time - now
            # 计算预计完成时间
            finish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
            # 打印剩余时间和预计完成时间
            print(f"剩余时间: {int(remaining_time)} 秒 | 预计结束时间: {finish_time}, 输入 \'q\' 以跳过", end="\r")
            time.sleep(1)
            seconds -= 1

        if not stop_event.is_set():
            print("\n时间到")
            countdown_finished_event.set()

    def check_exit():
        # 监听键盘输入，按 'q' 停止倒计时
        while not countdown_finished_event.is_set():
            if sys.stdin in select.select([sys.stdin], [], [], 1)[0]:  # 使用 select 监听输入
                input_char = sys.stdin.read(1).strip()  # 读取输入字符
                if input_char.lower() == 'q':
                    print("\n手动停止计时")
                    stop_event.set()  # 触发事件停止倒计时
                    break  # 停止监听输入，后续程序继续执行
        # print("计时结束，手动停止线程已退出")

    # 创建线程监听键盘输入
    exit_thread = threading.Thread(target=check_exit)
    exit_thread.daemon = True  # 设置为守护线程，使主线程结束时它自动退出
    exit_thread.start()

    # 启动倒计时
    countdown(seconds)