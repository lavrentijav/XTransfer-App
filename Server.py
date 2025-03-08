import hashlib
import os
import queue
import socket as sk
import threading
import time
import io

from tqdm import tqdm

import Check
import Process
from LocalizationForVersion_V0_0_2 import Languages as LFV
from SocketController import SocketController

GetSize = os.path.getsize
PathJoin = os.path.join

BASEDIR = "ServerCache"


def torrent_server(skcon: SocketController, progress_bar: queue.Queue, chunks: queue.Queue, open_file: io.BytesIO, work: bool = True):
    while not work:
        time.sleep(0.1)
    while not chunks.empty():

        cid, max_b_size, b_num = chunks.get()
        open_file.seek(b_num)

        packet = open_file.read(max_b_size)
        skcon.send_str("MOREDATA")
        skcon.recv_str()

        val = "UNVALID"
        while val == "UNVALID":
            skcon.send_str("HASHSIN")
            skcon.recv_str()
            skcon.send_str("HASH1")
            skcon.recv_str()
            skcon.send_str(hashlib.md5(packet).hexdigest())
            skcon.recv_str()
            skcon.send_str("HASH2")
            skcon.recv_str()
            skcon.send_str(hashlib.md5(packet).hexdigest())
            val = skcon.recv_str()

        skcon.send_str("DATAID")
        skcon.recv_str()
        skcon.send_list([b_num, len(packet)])
        skcon.recv_str()

        val = "UNVALID"
        while val == "UNVALID":
            skcon.send_str("DATA")
            skcon.recv_str()
            skcon.send_bin(packet)
            skcon.recv_str()
            skcon.send_str("VALIDATION")
            val = skcon.recv_str()
        progress_bar.put(max_b_size)
    else:
        skcon.send_str("END")
        skcon.close()
        open_file.close()


def start(file: str,
          ip: str = "127.0.0.1", port: int = 55500, max_ports: int = 4, max_packet_size: int = 16384, language: str = "en"):

    TRANSLATOR = LFV(language)

    if not os.path.exists(file):
        print(TRANSLATOR.get_text("FileNotFound"))
        time.sleep(10)
        exit(1)

    if not Check.check_port(ip, port):
        print(TRANSLATOR.get_text("IPNotAvailable") % (ip, port))
        time.sleep(10)
        exit(1)

    chunks = queue.Queue()

    for i in range(Process.calculate_number_of_chunks(file, max_packet_size)):
        chunks.put([i, max_packet_size, i * max_packet_size])

    file_hash = Process.calculate_file_hash(file, "md5", info=TRANSLATOR.get_text("CalcHash"))
    file_size = GetSize(file)

    file_name = Check.get_name_from_path(file)

    print(TRANSLATOR.get_text("ProcessedSuccess"))
    socket = sk.socket()
    socket.bind((ip, port))
    socket.listen(1)
    ports = []
    min_port = 49152
    max_port = 65535

    t_port = min_port - 1

    FPbar = tqdm(total=max_ports, desc=TRANSLATOR.get_text("FindPorts"), ascii=True, unit="Port", unit_scale=True,
                 dynamic_ncols=True, colour="green")

    while len(ports) < max_ports and t_port < max_port:
        t_port += 1
        if Check.check_port(ip, t_port):
            ports.append(t_port)
            FPbar.update()

    FPbar.close()
    if t_port == max_port:
        print(TRANSLATOR.get_text("PortsFound") % len(ports))

    print(TRANSLATOR.get_text("ServerStarted") % (ip, port))
    info_socket, addr = socket.accept()
    print(TRANSLATOR.get_text("Connected") % (list(addr)[0], list(addr)[1]))
    infocon = SocketController(info_socket)
    time.sleep(0.1)

    IRbar = tqdm(total=5, desc=TRANSLATOR.get_text("SendInfo"), ascii=True, unit="i", unit_scale=True,
                 dynamic_ncols=True, colour="green")
    infocon.recv_str()
    infocon.send_list(ports)
    IRbar.update(1)

    infocon.recv_str()
    infocon.send_str(file_hash)
    IRbar.update(1)

    infocon.recv_str()
    infocon.send_str(file_name)
    IRbar.update(1)

    infocon.recv_str()
    infocon.send_float(max_packet_size)
    IRbar.update(1)

    infocon.recv_str()
    infocon.send_float(file_size)
    IRbar.update(1)

    IRbar.close()

    threads = []

    work = False

    PQueue = queue.Queue()
    for i in range(len(ports)):
        port = ports[i]

        s = sk.socket()
        s.bind((ip, port))
        s.listen(1)

        infocon.send_str("CONNECT")
        opened_file = open(file, "rb")

        temp_socket, _ = s.accept()

        skcontroller = SocketController(temp_socket)

        infocon.recv_str()

        torrent_server_thread = threading.Thread(target=torrent_server, args=(
            skcontroller, PQueue, chunks, opened_file, lambda work: work),
                                                 name=f"ServerTorrentThreadPort{t_port}")
        torrent_server_thread.start()

        threads.append(torrent_server_thread)

    infocon.send_str("WORK")

    infocon.close()

    start_time = time.perf_counter()

    PbarTH = threading.Thread(target=Process.update_progress_bar, args=(file_size, PQueue, "Send File", "B"))
    PbarTH.start()

    work = True

    for thread in threads:
        thread.join()

    PbarTH.join()

    stop_time = time.perf_counter()

    all_time = round(stop_time - start_time, 3)

    if all_time <= 0.01:
        all_time += 1

    transfer_rate = Check.get_size_in_optimum_unit(file_size / all_time, min_unit='B/s', step=1024)

    print(TRANSLATOR.get_text("TransferSpeed") % ' '.join(list(map(str, transfer_rate.values()))))

    time.sleep(10)