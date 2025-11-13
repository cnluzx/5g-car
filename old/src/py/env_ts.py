import os
import subprocess

def main():

    ###############################################
    ##################环境变量检查##################
    ###############################################
    # 获取并打印 PATH 环境变量
    path = os.getenv('PATH')
    if path:
        print(f"PATH: {path}")
    else:
        print("PATH environment variable not found.")

    # 获取并打印 HOME 环境变量
    home = os.getenv('HOME')
    if home:
        print(f"HOME: {home}")
    else:
        print("HOME environment variable not found.")

    # 获取并打印 PYTHONPATH 环境变量
    pythonpath = os.getenv('PYTHONPATH')
    if pythonpath:
        print(f"PYTHONPATH: {pythonpath}")
    else:
        print("PYTHONPATH environment variable not found.")


    ###################################################
    #################测试Python YOLO脚本################
    ###################################################
    # 执行Python脚本并将输出重定向到res.txt文件
    # 使用subprocess.run更安全、更灵活
    
    with open('res.txt', 'w') as f:
        subprocess.run(
            ['/usr/bin/python', '/home/pi/g5g-new/yolo.py'],
            stdout=f,
            stderr=subprocess.STDOUT
        )

if __name__ == '__main__':
    main()
