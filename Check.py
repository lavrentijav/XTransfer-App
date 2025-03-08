import socket as sk
import os

GetSize = os.path.getsize
PathJoin = os.path.join


def check_port(ip: str, port: int):
    sock = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    sock.settimeout(1)  # Устанавливаем таймаут в 1 секунду
    try:
        sock.bind((ip, port))
    except OSError:
        return False
    finally:
        sock.close()
    return True


def get_size_in_optimum_unit(size, min_unit="bytes", step=1000):
    size_units = ["", "Kilo", "Mega", "Giga", "Tera", "Peta", "Exa", "Zetta", "Yotta"]

    new_sizes = [size]

    for i in range(1, 9):
        new_sizes.append(round(size / (step ** i), 3))
    
    for i in range(8):
        did = 8 - i

        if new_sizes[did] >= 0.5:
            return {"count": new_sizes[did], "unit": size_units[did] + min_unit}
    
    return {"count": size, "unit": min_unit}


def ensure_path_exists(path):
    if os.path.isabs(path):
        full_path = path
    else:
        full_path = os.path.join(os.getcwd(), path)

    full_path = os.path.normpath(full_path)

    if not os.path.exists(full_path):
        os.makedirs(full_path)

    return full_path


def get_name_from_path(path: str):
    return os.path.basename(path)


def port_is_free(test_host="127.0.0.1", port=1024):
    sock = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    try:
        sock.bind((test_host, port))
        sock.close()
        return port
    except OSError:
        return -1
