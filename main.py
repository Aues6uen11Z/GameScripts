import argparse
import json
import logging
import subprocess
import threading
import time
from pathlib import Path

import win32api
import win32job
import win32process

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%H:%M:%S",
)


class JobObjectManager:
    """管理Windows作业对象，用于控制进程及其子进程"""

    def __init__(self, command):
        self.command = command
        self.job = None
        self.proc_info = None
        self.pid = None

    def start(self):
        """创建job object并启动进程"""
        # 创建Job对象，配置为关闭时终止所有子进程
        self.job = win32job.CreateJobObject(None, "")
        extended_info = win32job.QueryInformationJobObject(
            self.job, win32job.JobObjectExtendedLimitInformation
        )
        extended_info["BasicLimitInformation"]["LimitFlags"] = (
            win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        win32job.SetInformationJobObject(
            self.job,
            win32job.JobObjectExtendedLimitInformation,
            extended_info,
        )

        # 启动进程（初始为暂停状态）
        si = win32process.STARTUPINFO()
        self.proc_info = win32process.CreateProcess(
            None,
            self.command,
            None,
            None,
            True,
            win32process.CREATE_SUSPENDED | win32process.CREATE_BREAKAWAY_FROM_JOB,
            None,
            None,
            si,
        )

        # 记录PID并将进程添加到Job
        self.pid = self.proc_info[2]
        win32job.AssignProcessToJobObject(self.job, self.proc_info[0])

        # 恢复进程执行
        win32process.ResumeThread(self.proc_info[1])
        logging.info(f"主进程 PID: {self.pid}")

    def kill(self):
        """终止Job及其所有相关进程"""
        if self.job:
            try:
                win32api.CloseHandle(self.job)
                self.job = None
                logging.info("已通过 Job Object 终止整个进程树")
            except Exception as e:
                logging.error(f"关闭 Job Object 失败: {e}")

    def has_active_processes(self):
        """检查Job中是否还有活跃进程"""
        if not self.job:
            return False

        try:
            stats = win32job.QueryInformationJobObject(
                self.job, win32job.JobObjectBasicAccountingInformation
            )
            return stats["TotalProcesses"] > 0
        except Exception as e:
            logging.warning(f"无法查询 Job 状态: {e}")
            return False


def read_stream(stream, callback):
    """持续读取流并将每行传递给回调函数"""
    for line in iter(stream.readline, b""):
        callback(line)
    stream.close()


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="游戏进程管理工具")
    parser.add_argument("option", help="选择要启动的游戏: 0=原神, 1=绝区零")
    args = parser.parse_args()

    # 加载配置
    config_path = Path("./config/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 根据选项设置命令和超时时间
    if args.option == "0":
        game_config = config["游戏"]["原神"]["游戏设置"]
        cmd = f"{game_config['BetterGI路径']} startOneDragon"
        timeout = game_config["最长运行时间"]
    elif args.option == "1":
        game_config = config["游戏"]["绝区零"]["游戏设置"]
        cmd = game_config["调度器路径"]
        timeout = game_config["最长运行时间"]

    # 验证并处理超时值
    try:
        timeout = int(timeout)
        timeout = timeout if timeout > 0 else -1
    except (ValueError, TypeError):
        timeout = -1

    logging.info(f"Command: {cmd}")
    logging.info(f"Timeout: {timeout} 分钟")

    # 启动Job管理器
    job_manager = JobObjectManager(cmd)
    job_manager.start()

    # 处理进程输出
    def handle_output(line):
        if line:
            logging.info(line.strip())

    # 启动Popen获取输出
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        text=True,  # 使用text替代universal_newlines
        encoding="utf-8",
    )

    # 启动线程读取输出
    output_thread = threading.Thread(
        target=read_stream, args=(proc.stdout, handle_output), daemon=True
    )
    output_thread.start()

    # 监控进程，处理超时
    start_time = time.time()
    try:
        while True:
            if not job_manager.has_active_processes():
                logging.info("进程正常结束")
                break

            if timeout > 0 and (time.time() - start_time > timeout * 60):
                logging.info("运行超时，正在终止进程...")
                job_manager.kill()
                break

            time.sleep(10)
    finally:
        # 确保线程正常结束
        output_thread.join(timeout=1)


if __name__ == "__main__":
    main()
