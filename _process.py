import hashlib
import os
import queue
import time
import sys

import socket as sk
from tqdm import tqdm

GetSize = os.path.getsize
PathJoin = os.path.join


def port_is_free(ip: str, port: int):
    sock = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    sock.settimeout(1)  # Устанавливаем таймаут в 1 секунду
    try:
        sock.bind((ip, port))
    except OSError:
        return False
    finally:
        sock.close()
    return True


def num_in_optimum_unit(size, min_unit="bytes", step=1000):
    size_units = ["", "Kilo", "Mega", "Giga", "Tera", "Peta", "Exa", "Zetta", "Yotta"]

    new_sizes = [size]

    for i in range(1, 9):
        new_sizes.append(round(size / (step ** i), 3))

    for i in range(8):
        did = 8 - i

        if new_sizes[did] >= 0.5:
            return {"count": new_sizes[did], "unit": size_units[did] + min_unit}

    return {"count": size, "unit": min_unit}


def get_name_from_path(path: str):
    return os.path.basename(path)


def create_large_binary_file(filename, size_in_bytes, info: str = "create file"):
    with tqdm(total=size_in_bytes, unit="B", unit_scale=True, desc=info, ascii=True, colour="green",
              unit_divisor=1024, file=sys.stdout) as pbar:
        with open(filename, 'wb') as f:
            # Записываем данные по частям, чтобы не загружать весь файл в память
            chunk_size = 1024 * 1024 * 4  # 1 МБ за раз
            for _ in range(size_in_bytes // chunk_size):
                f.write(b'\0' * chunk_size)  # Записываем 1 МБ нулей
                pbar.update(chunk_size)
            # Записываем оставшиеся байты, если они есть
            remaining_bytes = size_in_bytes % chunk_size
            pbar.update(remaining_bytes)
            if remaining_bytes > 0:
                f.write(b'\0' * remaining_bytes)


def calculate_file_hash(file_path, hash_algorithm='sha1', info: str = "Calculate Hash"):
    hash_func = hashlib.new(hash_algorithm)

    with open(file_path, 'rb') as f:
        with tqdm(total=GetSize(file_path), unit="B", unit_scale=True, desc=info,
                  ascii=True, colour="green", unit_divisor=1024, file=sys.stdout) as pbar:
            while chunk := f.read(1024 * 1024 * 4):
                hash_func.update(chunk)
                pbar.update(len(chunk))

    return hash_func.hexdigest()


def calculate_number_of_chunks(file_path, chunk_size=4096):
    file_size = os.path.getsize(file_path)
    number_of_chunks = (file_size + chunk_size - 1) // chunk_size
    return number_of_chunks


def update_progress_bar(total_size, progress_queue: queue.Queue, info, unit_div: int = 1000, unit: str = "it",
                        work: bool = True):
    with tqdm(total=total_size, unit=unit, unit_scale=True, desc=info, ascii=True, maxinterval=1,
              mininterval=0.05, colour="green", unit_divisor=unit_div, file=sys.stdout) as pbar:

        brk = 0
        time.sleep(2)
        while work:  # Измените условие на work
            if progress_queue.empty():
                brk += 1
                if brk > 100:
                    break
                else:
                    continue
            brk = 0
            chunk_size = sum(progress_queue.queue)
            progress_queue.queue.clear()
            pbar.update(chunk_size)

            time.sleep(0.1)
