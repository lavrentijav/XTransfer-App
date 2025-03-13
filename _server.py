import hashlib
import json
import os
import queue
import socket
import socket as sk
import threading
import time
import io
import logging
import sys

from tqdm import tqdm
import _process as xtlib
from _localization import Languages as Localization

GetSize = os.path.getsize
PathJoin = os.path.join

BASEDIR = "ServerCache"


def dumps(data):
    return json.dumps(data).encode("utf-8")


def loads(data):
    return json.loads(data.decode("utf-8"))


def is_json(data):
    try:
        json.loads(data.decode("utf-8"))
    except ValueError:
        return False
    return True


def torrent_server(conn: socket.socket, progress_bar: queue.Queue, chunks: queue.Queue, open_file: io.BytesIO,
                   work: bool = True):
    while not work:
        time.sleep(0.1)

    while True:

        try:
            cid, max_b_size, byte_num = chunks.get(timeout=0.01)
        except queue.Empty:
            break

        conn.send(b"moreData")
        conn.recv(1024)

        open_file.seek(byte_num)

        packet = open_file.read(max_b_size)

        chunk_hash = hashlib.md5(packet).hexdigest()

        data = {
            "byte": byte_num,
            "hash": chunk_hash
        }
        conn.send(dumps(data))

        valid = conn.recv(1024)

        while valid == b"invalid":
            conn.send(packet)

            valid = conn.recv(1024)

        progress_bar.put(len(packet))

    conn.send(b"notData")
    conn.recv(1024)

    open_file.close()
    conn.close()


def start(file: str,
          ip: str = "127.0.0.1", port: int = 55500, max_threads: int = 4, max_packet_size: int = 16384,
          language: str = "en"):
    TRANSLATOR = Localization(language)

    if not os.path.exists(file):
        logging.critical(TRANSLATOR.get_text("FileNotFound") % (file,))
        time.sleep(10)
        exit(1)

    if not xtlib.port_is_free(ip, port):
        logging.critical(TRANSLATOR.get_text("IPNotAvailable") % (str(ip), str(port)))
        time.sleep(10)
        exit(1)

    chunks = queue.Queue()

    for i in range(xtlib.calculate_number_of_chunks(file, max_packet_size)):
        chunks.put([i, max_packet_size, i * max_packet_size])

    file_hash = xtlib.calculate_file_hash(file, "md5", info=TRANSLATOR.get_text("CalcHash"))
    file_size = GetSize(file)

    file_name = xtlib.get_name_from_path(file)

    logging.info(TRANSLATOR.get_text("ProcessedSuccess"))
    my_conn = sk.socket()
    my_conn.bind((ip, port))
    my_conn.listen(1)

    min_port = 49152
    max_port = 65535

    t_port = min_port - 1

    transfer_ports = []

    FPbar = tqdm(total=max_threads, desc=TRANSLATOR.get_text("FindPorts"), ascii=True, unit="Port", unit_scale=True,
                 dynamic_ncols=True, colour="green", file=sys.stdout)

    while t_port < max_port and len(transfer_ports) < max_threads:
        t_port += 1
        if xtlib.port_is_free(ip, t_port):
            transfer_ports.append(t_port)
            FPbar.update()

    FPbar.close()

    logging.info(TRANSLATOR.get_text("ServerStarted") % (ip, port))

    info_socket, addr = my_conn.accept()
    logging.info(TRANSLATOR.get_text("Connected") % (list(addr)[0], list(addr)[1]))
    time.sleep(0.1)

    server_info = {
        "maxThreads": max_threads,
        "fileHash": file_hash,
        "fileName": file_name,
        "fileSize": file_size,
        "maxPacketSize": max_packet_size,
        "transferPorts": transfer_ports,
    }

    info_socket.send(dumps(server_info))

    client_info = loads(info_socket.recv(16384))

    max_threads = min(max_threads, client_info["maxThreads"])

    transfer_sockets = []

    for i in range(max_threads):

        transfer_socket = sk.socket()
        transfer_socket.bind((ip, transfer_ports[i]))
        transfer_socket.listen(1)

        info_socket.send(b"connect")

        transfer_socket, addr = transfer_socket.accept()

        transfer_sockets.append(transfer_socket)

        isConnect = info_socket.recv(1024)

        if isConnect != b"connected":
            info_socket.send(b"close")
            info_socket.close()
            transfer_socket.close()

            return

    threads = []

    work = False

    PQueue = queue.Queue()

    for i in range(max_threads):
        opened_file = open(file, "rb")

        torrent_server_thread = threading.Thread(target=torrent_server,
                                                 args=(
                                                     transfer_sockets[i], PQueue, chunks, opened_file,
                                                     lambda work: work),
                                                 name=f"ServerTorrentThread{i}")
        torrent_server_thread.start()

        threads.append(torrent_server_thread)

    start_time = time.perf_counter()

    PbarTH = threading.Thread(target=xtlib.update_progress_bar, args=(file_size, PQueue, "Send File", 1024, "B"))

    info_socket.recv(1024)
    info_socket.close()

    work = True
    PbarTH.start()

    for thread in threads:
        thread.join()

    PbarTH.join()

    stop_time = time.perf_counter()

    all_time = round(stop_time - start_time, 3)

    if all_time <= 0.01:
        all_time += 1

    transfer_rate = xtlib.num_in_optimum_unit(file_size / all_time, min_unit='B/s', step=1024)

    logging.info(TRANSLATOR.get_text("TransferSpeed") % ' '.join(list(map(str, transfer_rate.values()))))

    time.sleep(10)
