import os
import sys
import subprocess


class ProcessManager:
    @staticmethod
    def get_main_script_path():
        """获取 main.py 的绝对路径"""
        # 假设 main.py 在项目根目录，即 launcher 的上一级目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        return os.path.join(project_root, 'main.py')

    @staticmethod
    def run_visualization(data_folder):
        """
        启动 Pygame 可视化进程
        :param data_folder: 数据文件夹路径
        :return: (bool, str) 是否成功，错误信息
        """
        main_script = ProcessManager.get_main_script_path()

        if not os.path.exists(main_script):
            return False, f"未找到主程序文件：\n{main_script}"

        if not os.path.exists(data_folder):
            return False, f"数据文件夹不存在：\n{data_folder}"

        try:
            # 使用当前 Python 解释器运行 main.py
            # stdin=subprocess.DEVINIT 防止子进程抢占输入
            subprocess.Popen(
                [sys.executable, main_script, data_folder],
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            return True, "启动成功"
        except Exception as e:
            return False, f"启动进程失败：\n{str(e)}"
