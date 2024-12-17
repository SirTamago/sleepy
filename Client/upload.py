import requests
import pygetwindow as gw
import psutil
import time
import win32gui
import win32process

# 服务器URL
SERVER_URL = "YourServerIP:9010/set"
SECRET = "YourSecret"  # 用于验证的密钥

# 设定特殊程序名及对应返回的预设值
SPECIAL_APP_NAMES = {
    "QQ.exe": "QQ",
    "WeChat.exe": "微信"
}

replace_dict = {
    "YourServerIP": "不给看",
}


# 定时获取前台应用并上传
def get_foreground_app():
    try:
        # 获取当前前台窗口的标题
        window = gw.getWindowsWithTitle(gw.getActiveWindowTitle())[0]
        hwnd = window._hWnd  # 获取窗口的句柄

        # 使用 win32process 获取进程 ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # 使用 psutil 获取进程名称
        process = psutil.Process(pid)
        process_name = process.name()  # 获取进程名称

        # 检查是否是特定的程序名称，若是，则返回预设值
        if process_name in SPECIAL_APP_NAMES:
            return SPECIAL_APP_NAMES[process_name]
        else:
            # 获取窗口标题并进行替换
            window_title = window.title
            # 遍历替换字典，替换窗口标题中的指定字符串
            for target, replacement in replace_dict.items():
                window_title = window_title.replace(target, replacement)
            return window_title
    except Exception as e:
        print(f"Error getting foreground app: {e}")
        return None


def upload_foreground_app(current_app):
    # 上传到服务器
    params = {
        'secret': SECRET,
        'status': 0,  # 表示有应用正在运行
        'app_name': current_app,
        'device_type': 'computer'  # 表明是电脑端上传
    }
    try:
        response = requests.get(SERVER_URL, params=params)
        print(f"Uploaded app name: {current_app}, Response: {response.text}")
    except Exception as e:
        print(f"Error uploading: {e}")


def monitor_foreground_app():
    last_app = None  # 用于保存上次的前台应用
    while True:
        app_name = get_foreground_app()
        if app_name:
            # 如果当前应用和上次应用不同，则上传新的应用信息
            if app_name != last_app:
                print(f"Foreground app changed: {app_name}")
                upload_foreground_app(app_name)
                last_app = app_name  # 更新上次的应用名
        else:
            # 如果没有前台应用，上传状态1
            if last_app != "No Application":
                print("No application is currently running.")
                upload_foreground_app("No Application")
                last_app = "No Application"  # 更新为没有应用的状态

        time.sleep(1)  # 每秒检查一次前台应用


def main():
    print("Starting application monitor...")
    try:
        monitor_foreground_app()
    except KeyboardInterrupt:
        # 程序退出时上传 status=1，表示没有应用在运行
        print("Exiting program, uploading status=1 (No Application running).")
        upload_foreground_app("没开电脑")


if __name__ == "__main__":
    main()
