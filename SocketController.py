import socket as sk
import zlib
from typing import Union

class SocketController():

    def __init__(self, work_socket: sk.socket):
        self.socket = work_socket
        return

    def close(self):
        self.socket.close()

    def list_from_bin(self, binary_list: Union[bin, bytearray, bytes]) -> list:
        type_str = binary_list[:1]
        binary_list = binary_list[1:]

        if type_str == b"s":
            type_object = str
        elif type_str == b"f":
            type_object = float
        elif type_str == b"l":
            type_object = list
        elif type_str == b"d":
            type_object = dict
        else:
            raise ValueError("data is broken")

        recv_list = []

        for item in binary_list.split(b"&nO&"):
            if item == b"":
                continue
            if type_object == str:
                item = item.decode("utf-8")
                recv_list.append(str(item))
            if type_object == float:
                item = item.decode("utf-8")
                recv_list.append(float(item))
            elif type_object == list:
                recv_list.append(self.list_from_bin(item))
            elif type_object == dict:
                recv_list.append(self.dict_from_bin(item))
        return recv_list

    def dict_from_bin(self, binary_dict: Union[bin, bytearray, bytes]) -> dict:
        key_type_str = binary_dict[:1]
        value_type_str = binary_dict[1:2]
        binary_dict = binary_dict[2:]

        if key_type_str == b"s":
            key_type_object = str
        elif key_type_str == b"f":
            key_type_object = float
        elif key_type_str == b"l":
            key_type_object = list
        elif key_type_str == b"d":
            key_type_object = dict
        elif key_type_str == b"b":
            key_type_object = bin
        else:
            raise ValueError("data is broken")

        if value_type_str == b"s":
            value_type_object = str
        elif value_type_str == b"f":
            value_type_object = float
        elif value_type_str == b"l":
            value_type_object = list
        elif value_type_str == b"d":
            value_type_object = dict
        elif value_type_str == b"b":
            value_type_object = bin

        else:
            raise ValueError("data is broken")

        recv_dict = {}

        items = binary_dict.split(b"&nI&")

        for item in items:
            if item == b"":
                continue
            key: bin = item.split(b"&kV&")[0]
            value: bin = item.split(b"&kV&")[1]
            
            
            if item == b"&kV&":
                continue

            if key_type_object == str:
                key = key.decode("utf-8")
                key = str(key)
            if key_type_object == float:
                key = key.decode("utf-8")
                key = float(key)
            if key_type_object == bin:
                key = key
            elif key_type_object == list:
                key = self.list_from_bin(key)
            elif key_type_object == dict:
                key = self.dict_from_bin(key)

            if value_type_object == str:
                value = value.decode("utf-8")
                value = str(value)
            if value_type_object == float:
                value = value.decode("utf-8")
                value = float(value)
            if value_type_object == bin:
                value = value
            elif value_type_object == list:
                value = self.list_from_bin(value)
            elif value_type_object == dict:
                value = self.dict_from_bin(value)

            recv_dict.update({key: value})

        return recv_dict

    def list_to_bin(self, _list: list) -> bin:
        same_type = all(isinstance(x, type(_list[0])) for x in _list)
        if not same_type:
            raise TypeError("All elements in the list must be of the same type.")

        list_type = type(_list[0])

        bin_list = b""
        if list_type == int or list_type == float:
            bin_list += b"f"
        elif list_type == str:
            bin_list += b"s"
        elif list_type == list:
            bin_list += b"l"
        elif list_type == dict:
            bin_list += b"d"
        elif list_type == bin:
            bin_list += b"b"
        else:
            raise TypeError(f"obj {list_type} is not supported. Supported obj: float, int, list, dict, bin")
        
        for value in _list:
            bin_list += b"&nO&"
            if list_type == bin:
                bin_list += value
            elif list_type == str:
                bin_list += str(value).encode("utf-8")
            elif list_type == int or list_type == float:
                bin_list += str(value).encode("utf-8")
            elif list_type == list:
                bin_list += self.list_to_bin(value)
            elif list_type == dict:
                bin_list += self.dict_to_bin(value)

        return bin_list

    def dict_to_bin(self, _dict: dict) -> bin:
        type_key = all(isinstance(x, type(list(_dict.keys())[0])) for x in _dict.keys())
        type_value = all(isinstance(x, type(list(_dict.values())[0])) for x in _dict.values())
        
        type_key = type(list(_dict.keys())[0])
        type_value = type(list(_dict.values())[0])

        bin_dict = b""
        if type_key == int or type_key == float:
            bin_dict += b"f"
        elif type_key == str:
            bin_dict += b"s"
        elif type_key == list:
            bin_dict += b"l"
        elif type_key == dict:
            bin_dict += b"d"
        elif type_key == bin:
            bin_dict += b"b"
        else:
            raise TypeError(f"obj {type_key} is not supported. Supported obj: str, float, int, list, dict, bin")

        if type_value == int or type_value == float:
            bin_dict += b"f"
        elif type_value == str:
            bin_dict += b"s"
        elif type_value == list:
            bin_dict += b"l"
        elif type_value == dict:
            bin_dict += b"d"
        elif type_value == bin:
            bin_dict += b"b"
        else:
            raise TypeError(f"obj {type_value} is not supported. Supported obj: float, int, list, dict, bin")

        for item in _dict.items():
            bin_dict += b"&nI&"
            key, value = item
            if type_key == bin:
                bin_dict += key
            elif type_key == str:
                bin_dict += str(key).encode("utf-8")
            elif type_key == int or type_key == float:
                bin_dict += str(key).encode("utf-8")
            elif type_key == list:
                bin_dict += self.list_to_bin(key)
            elif type_key == dict:
                bin_dict += self.dict_to_bin(key)

            bin_dict += b"&kV&"

            if type_value == bin:
                bin_dict += value
            elif type_value == str:
                bin_dict += str(value).encode("utf-8")
            elif type_value == int or type_value == float:
                bin_dict += str(value).encode("utf-8")
            elif type_value == list:
                bin_dict += self.list_to_bin(value)
            elif type_value == dict:
                bin_dict += self.dict_to_bin(value)

        return bin_dict

    @staticmethod
    def unzip_bin(zip_binary: Union[bin, bytearray, bytes]):
        unzip_binary = zlib.decompress(zip_binary)
        return unzip_binary

    @staticmethod
    def zip_bin(unzip_binary: Union[bin, bytearray, bytes]):
        zip_binary = zlib.compress(unzip_binary)
        return zip_binary

    def recv_str(self, max_bin_len: int = 4096, zipping: bool = False) -> str:
        max_bin_len *= 1.1
        max_bin_len = int(max_bin_len)
        binary_str = self.socket.recv(max_bin_len)
        if zipping:
            binary_str = self.unzip_bin(binary_str)
        utf_string = binary_str.decode('utf-8')
        return utf_string

    def recv_float(self, max_bin_len: int = 1024, zipping: bool = False) -> float:
        max_bin_len *= 1.1
        max_bin_len = int(max_bin_len)
        binary_int = self.socket.recv(max_bin_len)

        if zipping:
            binary_int = self.unzip_bin(binary_int)

        integer = int(binary_int.decode("utf-8"))
        return integer

    def recv_list(self, max_bin_len: int = 4096, zipping: bool = False) -> list:
        max_bin_len *= 1.1
        max_bin_len = int(max_bin_len)
        binary_list = self.socket.recv(max_bin_len)

        if zipping:
            binary_list = self.unzip_bin(binary_list)

        return self.list_from_bin(binary_list)

    def recv_dict(self, max_bin_len: int = 8192, zipping: bool = False) -> dict:
        max_bin_len *= 1.1
        max_bin_len = int(max_bin_len)
        binary_dict = self.socket.recv(max_bin_len)

        if zipping:
            binary_dict = self.unzip_bin(binary_dict)

        return self.dict_from_bin(binary_dict)

    def recv_bin(self, max_bin_len: int = 8192, zipping: bool = False) -> bin:
        max_bin_len *= 1.1
        max_bin_len = int(max_bin_len)
        _bin = self.socket.recv(max_bin_len)
        
        if zipping:
            _bin = self.unzip_bin(_bin)
        
        return _bin

    def send_str(self, string: str, zipping: bool = False) -> int:
        bin_str = string.encode("utf-8")

        if zipping:
            bin_str = self.zip_bin(bin_str)

        return self.socket.send(bin_str)

    def send_float(self, integer: float, zipping: bool = False) -> int:
        bin_int = str(integer).encode("utf-8")

        if zipping:
            bin_int = self.zip_bin(bin_int)

        return self.socket.send(bin_int)

    def send_list(self, _list: list, zipping: bool = False) -> int:
        bin_list = self.list_to_bin(_list)

        if zipping:
            bin_list = self.zip_bin(bin_list)

        return self.socket.send(bin_list)

    def send_dict(self, _dict: dict, zipping: bool = False) -> int:
        bin_dict = self.dict_to_bin(_dict)
        
        if zipping:
            bin_dict = self.zip_bin(bin_dict)
        
        return self.socket.send(bin_dict)

    def send_bin(self, _bin: bin, zipping: bool = False) -> int:
        if zipping:
            _bin = self.zip_bin(_bin)
        
        return self.socket.send(_bin)