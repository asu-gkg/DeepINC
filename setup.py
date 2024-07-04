from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from distutils.errors import CompileError, DistutilsError, DistutilsPlatformError, LinkError, DistutilsSetupError, DistutilsExecError
import subprocess
import traceback
import os

server_lib = Extension('deep_inc.server.c_lib', [])

def has_rdma_header():
    ret_code = subprocess.call(
        "echo '#include <rdma/rdma_cma.h>' | cpp -H -o /dev/null 2>/dev/null", shell=True)
    if ret_code != 0:
        import warnings
        warnings.warn("\n\n No RDMA header file detected. Will disable RDMA for compilation! \n\n")
    return ret_code==0

def use_ucx():
    with_ucx = int(os.environ.get('WITH_UCX', 0))
    return with_ucx

def get_ucx_home():
    """ pre-installed ucx path """
    if should_build_ucx():
        return get_ucx_prefix()
    return os.environ.get('UCX_HOME', ucx_default_home)

def should_build_ucx():
    has_prebuilt_ucx = os.environ.get('UCX_HOME', '')
    return use_ucx() and not has_prebuilt_ucx

ucx_default_home = '/usr/local'
def get_ucx_prefix():
    """ specify where to install ucx """
    ucx_prefix = os.getenv('UCX_PREFIX', ucx_default_home)
    return ucx_prefix

def build_server(build_ext, options):
    server_lib.define_macros = options['MACROS']
    server_lib.include_dirs = options['INCLUDES']
    server_lib.sources = ['server/server.cc']
    server_lib.extra_compile_args = options['COMPILE_FLAGS'] + options['EXTRA_COMPILE_FLAGS']
    server_lib.extra_link_args = options['LINK_FLAGS']
    server_lib.extra_objects = options['EXTRA_OBJECTS']
    server_lib.library_dirs = options['LIBRARY_DIRS']

    build_ext.build_extension(server_lib)


# run the customize_compiler
class custom_build_ext(build_ext):
    def build_extensions(self):
        try:
            build_server(self)
        except:
            raise DistutilsSetupError('An ERROR occured while building the server module.\n\n'
                                      '%s' % traceback.format_exc())

setup(
    name='DeepINC',
    version='0.1',
    packages=find_packages(),
    install_requires=[

    ],
    cmdclass={
        'build_ext': custom_build_ext,
    },
    entry_points={
        'console_scripts': [
            
        ],
    },
)
