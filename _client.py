import hashlib
import os
import queue
import socket
import socket as sk
import threading
import time
import json
import logging

import _process as xtlib
from _localization import Languages as LFV

GetSize = os.path.getsize
PathJoin = os.path.join


class ThreadSafeFileWriter:
    def __init__(self, filename):
        self.file = open(filename, 'r+b')  # Открываем файл для чтения и записи
        self.lock = threading.Lock()  # Создаем блокировку

    def write(self, byte_num, packet):
        with self.lock:  # Захватываем блокировку
            self.file.seek(byte_num)  # Переходим к нужной позиции
            self.file.write(packet)  # Записываем данные

    def close(self):
        self.file.close()  # Закрываем фай


def isjson(data):
    try:
        json.loads(data.decode("utf-8"))
    except ValueError:
        return False
    return True


def dumps(data):
    return json.dumps(data).encode("utf-8")


def loads(data):
    return json.loads(data.decode("utf-8"))


def torrent_thread_client(conn: socket.socket, progress: queue.Queue, op_file: ThreadSafeFileWriter,
                          packet_size: int = 4096, work: bool = True):
    while not work:
        time.sleep(0.1)

    recv_buffer = int(packet_size * 2.5)

    while True:
        dt = conn.recv(1024)
        conn.send(b"ok")

        if dt != b"moreData":
            break
        response = conn.recv(recv_buffer)

        info = loads(response)

        packet_hash = ""
        packet = b""

        while info["hash"] != packet_hash:
            conn.send(b"invalid")
            packet = conn.recv(recv_buffer)
            packet_hash = hashlib.md5(packet).hexdigest()

        conn.send(b"valid")

        op_file.write(int(info["byte"]), packet)
        progress.put(len(packet))

    conn.close()


def receive_data(host='127.0.0.1', info_port=-1, save_dir: str = ".", language: str = "en"):
    TRANSLATOR = LFV(language)

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    my_socket = sk.socket()
    my_socket.connect((host, info_port))

    server_info = loads(my_socket.recv(8192))

    max_threads = server_info["maxThreads"]

    client_info = {
        "maxThreads": max_threads,
    }

    my_socket.send(dumps(client_info))

    file_name = server_info["fileName"]
    file_size = server_info["fileSize"]
    final_hash = server_info["fileHash"]
    block_size = server_info["maxPacketSize"]
    max_threads = min(server_info["maxThreads"], max_threads)
    transfer_ports = server_info["transferPorts"]
    transfer_sockets = []

    for i in range(max_threads):
        transfer_socket = sk.socket()
        my_socket.recv(1024)
        try:
            transfer_socket.connect((host, transfer_ports[i]))
            my_socket.send(b"connected")
            transfer_sockets.append(transfer_socket)

        except sk.error as e:
            my_socket.send(b"notConnect")
            my_socket.recv(1024)
            my_socket.close()
            transfer_socket.close()
            logging.info(TRANSLATOR.get_text("PortNotAvailable") % (host, transfer_ports[i]))
            my_socket.close()
            time.sleep(10)
            exit(1)

    save_name = PathJoin(save_dir, file_name)

    if os.path.exists(save_name):
        logging.warning(TRANSLATOR.get_text("downFileDel") + "\r")
        ask = input()
        while ask not in ["y", "n", "yes", "no"]:
            logging.warning(TRANSLATOR.get_text("downFileDelAnswerNotAllowed") % (ask,))
            logging.info(TRANSLATOR.get_text("downFileDel") + "\r")
            ask = input()

        max_id = 0

        for file in os.listdir(save_dir):
            if file.startswith(file_name):
                max_id += 1

        if ask in ["n", "no"]:
            file_name = file_name[::-1].replace(".", f" (new-{max_id})."[::-1], 1)[::-1]

        else:
            os.remove(save_name)

    save_name = PathJoin(save_dir, file_name)

    temp_name = PathJoin(save_dir, file_name[:file_name.rfind(".")] + ".crdownload")

    xtlib.create_large_binary_file(temp_name, file_size, info=TRANSLATOR.get_text("downProcess"))

    progress_queue = queue.Queue()

    bar = threading.Thread(target=xtlib.update_progress_bar,
                           args=(file_size, progress_queue, TRANSLATOR.get_text("ReceivingFile"), 1024, "B", True),
                           name="ProgressBarThread")

    threads = []
    work = False
    tmp_file = ThreadSafeFileWriter(temp_name)
    for i in range(max_threads):
        th = threading.Thread(target=torrent_thread_client,
                              args=(transfer_sockets[i], progress_queue, tmp_file, block_size, lambda work: work),
                              name=f"ClientTorrentThread{i}")
        th.start()
        threads.append(th)

    my_socket.send(b"ready")
    my_socket.close()

    work = True
    bar.start()

    start_time = time.perf_counter()

    for future in threads:
        future.join()

    stop_time = time.perf_counter()

    tmp_file.close()

    bar.join()
    all_time = round(stop_time - start_time, 3)

    if all_time <= 0.01:
        all_time += 1

    transfer_rate = xtlib.num_in_optimum_unit(file_size / all_time, min_unit='B/s', step=1024)

    logging.info(TRANSLATOR.get_text("TransferSpeed") % ' '.join(list(map(str, transfer_rate.values()))))

    time.sleep(0.1)
    file_hash = xtlib.calculate_file_hash(temp_name, "md5", TRANSLATOR.get_text("CalcHash"))

    logging.info(TRANSLATOR.get_text("DataTransferComplete"))
    logging.info(TRANSLATOR.get_text("HashCheck") + " " + str(file_hash == final_hash))

    os.rename(temp_name, save_name)

    time.sleep(10)
