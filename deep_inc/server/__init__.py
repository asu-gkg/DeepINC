import ctypes
import os
from deep_inc.common import get_ext_suffix

# TODO: implement the server logic
def run():
    print("__file__", __file__)
    dll_path = os.path.join(os.path.dirname(__file__),
                            'c_lib' + get_ext_suffix())
    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"Shared library {dll_path} not found")
    SERVER_LIB_CTYPES = ctypes.CDLL(dll_path, ctypes.RTLD_GLOBAL)
    print("SERVER_LIB_CTYPES", SERVER_LIB_CTYPES)
    SERVER_LIB_CTYPES.start_server()

# def run():
#     print("__file__", __file__)
#     dll_path = os.path.join(os.path.dirname(__file__),
#                             'c_lib.so')
#     if not os.path.exists(dll_path):
#         raise FileNotFoundError(f"Shared library {dll_path} not found")
#     SERVER_LIB_CTYPES = ctypes.CDLL(dll_path, ctypes.RTLD_GLOBAL)
#     print("SERVER_LIB_CTYPES", SERVER_LIB_CTYPES)
#     SERVER_LIB_CTYPES.start_server()

run()
