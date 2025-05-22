import os
import logging

def clear_logs(log_dir: str):
    """
    清除指定目录及其子目录下的所有 .log 文件。
    :param log_dir: 日志文件夹路径
    """
    if not os.path.exists(log_dir):
        print(f"日志目录 {log_dir} 不存在。")
        return

    try:
        for root, _, files in os.walk(log_dir):
            for file_name in files:
                if file_name.endswith(".log"):
                    file_path = os.path.join(root, file_name)
                    os.remove(file_path)
                    print(f"已删除日志文件: {file_path}")
        print("所有日志文件已清除。")
    except Exception as e:
        print(f"清除日志文件时发生错误: {str(e)}")

if __name__ == "__main__":
    # 设置日志目录路径
    log_directory = "src/chemistry_os/src/"  # 根据实际情况修改路径
    clear_logs(log_directory)