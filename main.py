import configparser
import os
import time
import logging
import sys

from _localization import Languages

DEBUG = True


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',   # Red
        'CRITICAL': '\033[41m', # Red background
    }
    RESET = '\033[0m'  # Reset to default color

    def format(self, record) -> str:
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


if DEBUG:
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter_ok = ColoredFormatter('%(levelname)s$: %(message)s')
    formatter_root = ColoredFormatter('%(levelname)#$: %(message)s')

    handler.setFormatter(formatter_ok)
    logger.addHandler(handler)
    logger.setLevel(DEBUG)

if "config.ini" not in os.listdir():
    conf = open("config.ini", "w")
    conf.write(
        f"""
[START]
allowStart = False
requestInfo = True
[Settings server]

file = test.txt
; the path to the file to send

maxPorts = {os.cpu_count() * 2}
; maximum number of threads to send (recommended [all processor cores] * 2)

hostIp = 0.0.0.0
; the IP address of the PC on which the file will be distributed (0.0.0.0 - all connected networks)

hostPort = 55500

maxPacketSize = 32768
; max data in 1 data packet in Bytes recommend 32768. MAX 65435
[Settings client]
savePath = .
hostIp = 127.0.0.1
hostPort = 55500
[Languages]
language = ru
; allowed en, ru, pl, it, es, zh 
"""
    )
    conf.close()

if __name__ == '__main__':

    config = configparser.ConfigParser()
    # Читаем файл конфигурации
    config.read('config.ini')

    current_language = config.get('Languages', 'LANGUAGE', fallback="en")

    start = config.get('START', 'allowStart', fallback="True")
    if start == "False":
        logging.error("read and configure the config.enable it, and also allow it to run using allowStart = True")
        time.sleep(10)
        exit(1)

    requestInfo = config.get('START', 'requestInfo', fallback="True")

    TRANSLATOR = Languages(current_language)

    logging.info(TRANSLATOR.get_text("GetMode"))
    logging.info(TRANSLATOR.get_text("GetOptions")+"\r")
    MOD = int(input())
    if MOD == 1:
        import _client

        logging.info(TRANSLATOR.get_text("ClientLoading"))

        if requestInfo == "True":
            # Извлекаем значения
            logging.info(TRANSLATOR.get_text("EnterSavePath")+"\r")
            save_path = input()
            if save_path == "":
                SAVE_PATH = config.get('Settings client', 'savePath', fallback=".")
            else:
                SAVE_PATH = save_path

            logging.info(TRANSLATOR.get_text("EnterServerIP")+"\r")

            host_ip = input()
            if host_ip == "":
                HOST_IP = config.get('Settings client', 'hostIp', fallback="127.0.0.1")
            else:
                HOST_IP = host_ip

            logging.info(TRANSLATOR.get_text("EnterMainPort")+"\r")

            host_port = input()
            if host_port == "":
                HOST_PORT = config.getint('Settings client', 'hostPort', fallback=55001)
            else:
                HOST_PORT = int(host_port)

            del save_path
            del host_ip
            del host_port

        else:
            SAVE_PATH = config.get('Settings client', 'savePath', fallback=".")
            HOST_IP = config.get('Settings client', 'hostIp', fallback="127.0.0.1")
            HOST_PORT = config.getint('Settings client', 'hostPort', fallback=55001)

        _client.receive_data(HOST_IP, HOST_PORT, SAVE_PATH, current_language)

    elif MOD == 2:
        import _server

        logging.info(TRANSLATOR.get_text("ServerLoading")+"\r")

        # Извлекаем значения
        if requestInfo == "True":

            logging.info(TRANSLATOR.get_text("EnterSendFilePath")+"\r")

            file = input()
            if file == "":
                FILE = config.get('Settings server', 'file', fallback=".")
            else:
                FILE = file

            logging.info(TRANSLATOR.get_text("EnterServerIP")+"\r")

            host_ip = input()
            if host_ip == "":
                HOST_IP = config.get('Settings server', 'hostIp', fallback="0.0.0.0")
            else:
                HOST_IP = host_ip

            logging.info(TRANSLATOR.get_text("EnterMainPort")+"\r")

            host_port = input()
            if host_port == "":
                HOST_PORT = config.getint('Settings server', 'hostPort', fallback=55001)
            else:
                HOST_PORT = int(host_port)

            logging.info(TRANSLATOR.get_text("EnterMaxPorts")+"\r")

            max_ports = input()
            if max_ports == "":
                MAX_PORTS = config.getint('Settings server', 'maxPorts', fallback=4)
            else:
                MAX_PORTS = int(max_ports)

            logging.info(TRANSLATOR.get_text("EnterMaxPacketSize") + "\r")

            max_pack_size = input()
            if max_pack_size == "":
                MAX_PACKET_SIZE = config.getint('Settings server', 'maxPacketSize', fallback=4096)
            else:
                MAX_PACKET_SIZE = int(max_pack_size)

            del host_port
            del max_ports
            del max_pack_size
            del host_ip
            del file

        else:
            FILE = config.get('Settings server', 'file', fallback=".")
            HOST_IP = config.get('Settings server', 'hostIp', fallback="0.0.0.0")
            HOST_PORT = config.getint('Settings server', 'hostPort', fallback=55001)
            MAX_PORTS = config.getint('Settings server', 'maxPorts', fallback=4)
            MAX_PACKET_SIZE = config.getint('Settings server', 'maxPacketSize', fallback=4096)

            # Выводим значения
            logging.info(TRANSLATOR.get_text("FilePath") % FILE)
            # logging.info(TRANSLATOR.get_text("PacketSize") % MAX_PACKET_SIZE)
            # logging.info(TRANSLATOR.get_text("HostIP") % HOST_IP)
            # logging.info(TRANSLATOR.get_text("HostPort") % HOST_PORT)
            # logging.info(TRANSLATOR.get_text("MaxPorts") % MAX_PORTS)

        _server.start(FILE, HOST_IP, HOST_PORT, MAX_PORTS, MAX_PACKET_SIZE, current_language)
