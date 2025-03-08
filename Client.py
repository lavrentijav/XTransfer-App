import hashlib
import os
import queue
import socket as sk
import threading
import time

from tqdm import tqdm

import Check
import Process
from LocalizationForVersion_V0_0_2 import Languages as LFV
from SocketController import SocketController

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


def torrent_thread_client(skcon: SocketController, progress: queue.Queue, op_file: ThreadSafeFileWriter,
                          packet_size: int = 4096, work: bool = True):
    while not work:
        time.sleep(0.1)

    work = skcon.recv_str()
    while work == "MOREDATA":
        skcon.send_str("OK")
        val = "UNVALID"

        hash_1 = ""
        while val == "UNVALID":
            skcon.recv_str()
            skcon.send_str("OK")
            skcon.recv_str()
            skcon.send_str("OK")
            hash_1 = skcon.recv_str()
            skcon.send_str("OK")
            skcon.recv_str()
            skcon.send_str("OK")
            hash_2 = skcon.recv_str()
            val = "VALID" if hash_1 == hash_2 else "UNVALID"
            skcon.send_str(val)

        valid_hash = hash_1
        del hash_1
        del hash_2

        skcon.recv_str()
        skcon.send_str("OK")
        byte_num, chunk_size = skcon.recv_list(8192)
        skcon.send_str("OK")

        packet = b""

        val = "UNVALID"
        while val == "UNVALID":
            skcon.recv_str()
            skcon.send_str("OK")
            packet = skcon.recv_bin(packet_size)
            skcon.send_str("OK")
            skcon.recv_str()
            packet_hash = hashlib.md5(packet).hexdigest()
            val = "VALID" if packet_hash == valid_hash else "UNVALID"
            skcon.send_str(val)

        op_file.write(int(byte_num), packet)
        progress.put(len(packet))

        work = skcon.recv_str()
    else:
        skcon.close()


def receive_data(host='127.0.0.1', info_port=-1, save_dir: str = ".", language: str = "en"):
    TRANSLATOR = LFV(language)

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    my_socket = sk.socket()
    my_socket.connect((host, info_port))

    infocon = SocketController(my_socket)

    IRbar = tqdm(total=6, desc=TRANSLATOR.get_text("ReceivingInfo"), ascii=True, unit="i", unit_scale=True,
                 dynamic_ncols=True, colour="green")

    infocon.send_str("Ports")
    ports = infocon.recv_list()
    IRbar.update(1)
    IRbar.update(1)
    infocon.send_str("FileHash")
    final_hash = infocon.recv_str()
    IRbar.update(1)
    infocon.send_str("FileName")
    file_name = infocon.recv_str()
    IRbar.update(1)
    infocon.send_str("BlockSize")
    block_size = int(infocon.recv_float() * 1.5)
    IRbar.update(1)
    infocon.send_str("FileSize")
    file_size = int(infocon.recv_float())
    IRbar.update(1)

    IRbar.close()



    save_name = PathJoin(save_dir, file_name)

    if os.path.exists(save_name):
        ask = input(TRANSLATOR.get_text("downFileDel"))
        while ask not in ["y", "n", "yes", "no"]:
            print(TRANSLATOR.get_text("downFileDelAnswerNotAllowed") % (ask,))
            input(TRANSLATOR.get_text("downFileDel"))

        if ask in ["n", "no"]:
            save_name = save_name[::-1].replace(".", " (new)."[::-1], 1)[::-1]

        else:
            os.remove(save_name)

    temp_name =  PathJoin(save_dir, file_name[:file_name.rfind(".")] + ".crdownload")

    Process.create_large_binary_file(temp_name, file_size, info=TRANSLATOR.get_text("downProcess"))

    progress_queue = queue.Queue()

    bar = threading.Thread(target=Process.update_progress_bar,
                           args=(file_size, progress_queue, TRANSLATOR.get_text("ReceivingFile"), "B", True),
                           name="ProgressBarThread")
    bar.start()

    threads = []
    work = False
    tmp_file = ThreadSafeFileWriter(temp_name)
    for port in ports:
        port = int(port)
        s = sk.socket()
        infocon.recv_str()
        s.connect((host, port))

        th = threading.Thread(target=torrent_thread_client,
                              args=(SocketController(s), progress_queue, tmp_file, block_size, lambda work: work),
                              name=f"ClientTorrentThreadPort{port}")
        th.start()
        threads.append(th)

        infocon.send_str("CONTINUE")

    infocon.recv_str()

    infocon.close()

    work = True

    start_time = time.perf_counter()

    for future in threads:
        future.join()

    tmp_file.close()

    stop_time = time.perf_counter()

    bar.join()
    all_time = round(stop_time - start_time, 3)

    if all_time <= 0.01:
        all_time += 1

    transfer_rate = Check.get_size_in_optimum_unit(file_size / all_time, min_unit='B/s', step=1024)

    print(TRANSLATOR.get_text("TransferSpeed") % ' '.join(list(map(str, transfer_rate.values()))))

    time.sleep(0.1)

    os.rename(temp_name, save_name)

    file_hash = Process.calculate_file_hash(save_name, "md5", TRANSLATOR.get_text("CalcHash"))

    print(TRANSLATOR.get_text("DataTransferComplete"))
    print(TRANSLATOR.get_text("HashCheck"), file_hash == final_hash)

    time.sleep(10)
