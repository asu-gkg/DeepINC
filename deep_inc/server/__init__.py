import ctypes
import os
from deep_inc.common import get_ext_suffix

# TODO: implement the server logic
def run():
    dll_path = os.path.join(os.path.dirname(__file__),
                            'c_lib' + get_ext_suffix())
    SERVER_LIB_CTYPES = ctypes.CDLL(dll_path, ctypes.RTLD_GLOBAL)
    SERVER_LIB_CTYPES.start_server()

run()
