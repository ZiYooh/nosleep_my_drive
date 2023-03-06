import os
import sys
import ctypes
import time
import pystray
import atexit

import mylogger

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem


def alert_basic(message):
    ctypes.windll.user32.MessageBoxW(None, message, "Nosleep My Drive", 0)


def alert_info(message):
    ctypes.windll.user32.MessageBoxW(None, message, "Nosleep My Drive", 64)


def alert_warn(message):
    ctypes.windll.user32.MessageBoxW(None, message, "Nosleep My Drive", 48)


def alert_stop(message):
    ctypes.windll.user32.MessageBoxW(None, message, "Nosleep My Drive", 16)


# 시스템 트레이 아이콘에서 프로그램 종료하기 위한 함수
def exit_process_with_pystray(myicon):
    myicon.notify("Nosleep My Drive를 종료합니다.")
    myicon.stop()
    os._exit(0)


def open_cur_dir():
    path = os.path.realpath('./')
    os.startfile(path)


# Logger Setting Start
logger = mylogger.set_logger()
sys.excepthook = mylogger.handle_exception
# Logger Setting End

MAX_RETRY_CONT = 5
RETRY_INTERVAL = 60

if __name__ == "__main__":
    logger.info("프로세스 시작")
    # pystray 관련 시작
    myimage = Image.open("icon.png")
    icon_name = "Nosleep My Drive"
    myicon = Icon(name=icon_name, title=icon_name)
    myicon.icon = myimage

    myicon.menu = Menu(
        MenuItem(
            "실행 폴더 열기",
            lambda: open_cur_dir()),
        MenuItem(
            "종료",
            lambda myicon: exit_process_with_pystray(myicon))
    )

    myicon.run_detached()
    # pystray 관련 끝

    set_time = None
    set_drive = None

    # 0) 설정파일 검사
    with open('setting.conf', 'r') as file:  # setting.conf 파일을 읽기 모드(r)로 열기
        line = None  # 변수 line을 None으로 초기화
        while line != '':
            line = file.readline().strip('\n')

            # 설정파일 내용 확인
            # 시간 설정 (최소 5분)
            if 'TIME=' in line:
                set_time = int(line.split('=')[1])

            # 드라이브 문자 설정
            if 'DRIVE=' in line:
                set_drive = line.split('=')[1]

        if set_time < 300:
            logger.warning(f"설정 시간({set_time})이 최소 동작 시간(300초=5분)보다 작습니다. 최소 동작 시간으로 작동합니다.")
            alert_warn(f"설정 시간({set_time})이 최소 동작 시간(300초=5분)보다 작습니다. 최소 동작 시간으로 작동합니다.")
            # set_time = 300

        logger.info(f"설정 시간: {set_time}")
        logger.info(f"설정 드라이브: {set_drive}")

    time.sleep(1)

    # 1) 드라이브 유무 확인
    # 1-1) 설정 횟수+시간 간격만큼 드라이브 탐색 재시도 (기본값 60초 간격으로 5회)
    cur_retry_count = 0
    drive_check_count = 0
    while cur_retry_count < MAX_RETRY_CONT:
        for i in range(len(set_drive)):
            temp_drive_path = f"{set_drive[i].upper()}:\\"

            if not os.path.isdir(temp_drive_path):
                logger.warning(f"{set_drive[i]}드라이브 인식 불가... {cur_retry_count+1}회째 시도중...")
            else:
                drive_check_count += 1

        if drive_check_count is len(set_drive):
            logger.info(f"드라이브 인식 완료. (DRIVE={set_drive})")
            break
        else:
            cur_retry_count += 1
            drive_check_count = 0
            if cur_retry_count is MAX_RETRY_CONT:
                logger.error(f"드라이브 문자 설정이 잘못되었거나 해당 드라이브를 인식할 수 없습니다. (DRIVE={set_drive})")
                alert_stop(f"드라이브 문자 설정이 잘못되었거나 해당 드라이브를 인식할 수 없습니다.\nDRIVE={set_drive}")
                exit_process_with_pystray(myicon)
            time.sleep(RETRY_INTERVAL)

    # 2) 더미파일 유무 확인
    for i in range(len(set_drive)):
        temp_dummy_path = f"{set_drive[i].upper()}:\\nosleep_dummy.txt"

        if not os.path.isfile(temp_dummy_path):
            logger.info(f"{set_drive[i]}드라이브 더미파일 생성")
            file = open(temp_dummy_path, 'w')
            file.write("Nosleep My Drive 더미 파일 입니다.")
            file.close()

    myicon.notify("Nosleep My Drive를 시작합니다.")

    while 1:
        try:
            for i in range(len(set_drive)):
                dummy_path = f"{set_drive[i].upper()}:\\nosleep_dummy.txt"
                # file = open(dummy_path, 'r')
                # line = file.read()
                # logger.info(line)
                # file.close()
                file = open(dummy_path, 'w')
                file.write("Nosleep My Drive 더미 파일 입니다.")
                time.sleep(5)
                file.close()
        except Exception as e:
            logger.error("오류가 발생하였습니다.")
            logger.error(e)
            alert_stop(f"오류가 발생하였습니다.\n{e}")
            exit_process_with_pystray(myicon)

        time.sleep(set_time)
