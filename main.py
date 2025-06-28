import argparse
import json
import logging
import subprocess
import threading
import time
from pathlib import Path

import win32api
import win32job
import win32con


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
        self.process = None
        self.output_thread = None

    def start(self):
        """创建job object并启动进程"""
        try:
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

            # 启动进程
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True,
                encoding="gbk",
            )

            # 记录PID
            self.pid = self.process.pid

            # 打开进程句柄并将进程添加到Job
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_ALL_ACCESS,
                False,
                self.pid,  # 使用win32con而不是win32process
            )
            win32job.AssignProcessToJobObject(self.job, process_handle)
            win32api.CloseHandle(process_handle)  # 关闭我们打开的句柄

            logging.info(f"主进程 PID: {self.pid}")

            return True
        except Exception as e:
            logging.error(f"启动进程失败: {e}")
            self.kill()  # 清理资源
            return False

    def start_output_monitoring(self, callback):
        """启动输出监控线程"""
        if self.process and self.process.stdout:

            def read_stream():
                for line in iter(self.process.stdout.readline, ""):
                    if line:
                        callback(line)
                self.process.stdout.close()

            self.output_thread = threading.Thread(target=read_stream, daemon=True)
            self.output_thread.start()

    def kill(self):
        """终止Job及其所有相关进程，清理资源"""
        # 关闭Job Object句柄
        if self.job:
            try:
                win32api.CloseHandle(self.job)
                logging.info("已终止整个进程树")
            except Exception as e:
                logging.error(f"关闭 Job Object 失败: {e}")
            finally:
                self.job = None

        # 关闭进程对象
        if self.process:
            try:
                self.process.terminate()
            except:  # noqa: E722
                pass
            self.process = None

    def job_info(self, stats):
        """获取当前Job中的进程详细信息"""
        logging.info(
            f"Job状态: 总进程数={stats['TotalProcesses']}, 活跃={stats['ActiveProcesses']}"
        )
        if stats["TotalProcesses"] > 0:
            try:
                # 获取Job中的进程列表（仅PID）
                process_ids = win32job.QueryInformationJobObject(
                    self.job, win32job.JobObjectBasicProcessIdList
                )

                if process_ids:
                    process_info = []
                    import psutil

                    try:
                        pid_to_name = {}
                        for pid in process_ids:
                            try:
                                p = psutil.Process(pid)
                                pid_to_name[pid] = p.name()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pid_to_name[pid] = "无法访问"

                        for pid in process_ids:
                            proc_name = pid_to_name.get(pid, "未知")
                            process_info.append(f"PID:{pid}({proc_name})")

                        processes_str = ", ".join(process_info)
                        logging.info(f"Job中的活跃进程: {processes_str}")
                    except Exception as e:
                        logging.warning(f"获取进程名称时出错: {e}")
                        processes_str = ", ".join([f"PID:{pid}" for pid in process_ids])
                        logging.info(f"Job中的活跃进程: {processes_str}")

            except Exception as e:
                logging.warning(f"无法获取Job中的进程列表: {e}")

    def has_active_processes(self):
        """检查Job中是否还有活跃进程"""
        if not self.job:
            return False

        try:
            stats = win32job.QueryInformationJobObject(
                self.job, win32job.JobObjectBasicAccountingInformation
            )
            # self.job_info(stats)
            return stats["ActiveProcesses"] > 0
        except Exception as e:
            logging.warning(f"无法查询Job状态: {e}")
            return False

    def wait_for_output_thread(self, timeout=1):
        """等待输出线程完成"""
        if self.output_thread and self.output_thread.is_alive():
            self.output_thread.join(timeout=timeout)

    def __del__(self):
        """析构函数，确保资源被清理"""
        self.kill()


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser()
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
    if not job_manager.start():
        return

    # 处理进程输出
    def handle_output(line):
        if line:
            print(line.strip())

    # 启动输出监控
    job_manager.start_output_monitoring(handle_output)

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
        # 确保资源被清理
        job_manager.kill()
        job_manager.wait_for_output_thread()


if __name__ == "__main__":
    main()
