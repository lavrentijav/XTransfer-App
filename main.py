import configparser
import os
import time

from LocalizationForVersion_V0_0_2 import Languages

DEBUG = False

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
        print("read and configure the config.enable it, and also allow it to run using allowStart = True")
        time.sleep(10)
        exit(1)

    requestInfo = config.get('START', 'requestInfo', fallback="True")

    TRANSLATOR = Languages(current_language)

    print(TRANSLATOR.get_text("GetMode"))
    MOD = int(input(TRANSLATOR.get_text("GetOptions")))
    if MOD == 1:
        print(TRANSLATOR.get_text("ClientLoading"))

        if requestInfo == "True":
            # Извлекаем значения
            save_path = input(TRANSLATOR.get_text("EnterSavePath"))
            if save_path == "":
                SAVE_PATH = config.get('Settings client', 'savePath', fallback=".")
            else:
                SAVE_PATH = save_path

            host_ip = input(TRANSLATOR.get_text("EnterServerIP"))
            if host_ip == "":
                HOST_IP = config.get('Settings client', 'hostIp', fallback="127.0.0.1")
            else:
                HOST_IP = host_ip

            host_port = input(TRANSLATOR.get_text("EnterMainPort"))
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

        def StartClient():
            import Client
            global HOST_IP, HOST_PORT, SAVE_PATH
            Client.receive_data(HOST_IP, HOST_PORT, SAVE_PATH, current_language)


        StartClient()

    elif MOD == 2:
        print(TRANSLATOR.get_text("ServerLoading"))

        # Извлекаем значения
        if requestInfo == "True":

            file = input(TRANSLATOR.get_text("EnterSendFilePath"))
            if file == "":
                FILE = config.get('Settings server', 'file', fallback=".")
            else:
                FILE = file

            host_ip = input(TRANSLATOR.get_text("EnterServerIP"))
            if host_ip == "":
                HOST_IP = config.get('Settings server', 'hostIp', fallback="0.0.0.0")
            else:
                HOST_IP = host_ip

            host_port = input(TRANSLATOR.get_text("EnterMainPort"))
            if host_port == "":
                HOST_PORT = config.getint('Settings server', 'hostPort', fallback=55001)
            else:
                HOST_PORT = int(host_port)

            max_ports = input(TRANSLATOR.get_text("EnterMaxPorts"))
            if max_ports == "":
                MAX_PORTS = config.getint('Settings server', 'maxPorts', fallback=4)
            else:
                MAX_PORTS = int(max_ports)

            max_pack_size = input(TRANSLATOR.get_text("EnterMaxPacketSize"))
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
            print(TRANSLATOR.get_text("FilePath") % FILE)
            # print(TRANSLATOR.get_text("PacketSize") % MAX_PACKET_SIZE)
            # print(TRANSLATOR.get_text("HostIP") % HOST_IP)
            # print(TRANSLATOR.get_text("HostPort") % HOST_PORT)
            # print(TRANSLATOR.get_text("MaxPorts") % MAX_PORTS)



        def StartServer():
            import Server
            global FILE, HOST_IP, HOST_PORT, MAX_PORTS, MAX_PACKET_SIZE
            Server.start(FILE, HOST_IP, HOST_PORT, MAX_PORTS, MAX_PACKET_SIZE, current_language)


        StartServer()
