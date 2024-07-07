from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from distutils.errors import CompileError, DistutilsError, DistutilsPlatformError, LinkError, DistutilsSetupError, \
    DistutilsExecError
import subprocess
import traceback
import os
import sys
import textwrap
import shlex

server_lib = Extension('deep_inc.server.c_lib', [])
extensions_to_build = [server_lib]


def has_rdma_header():
    ret_code = subprocess.call(
        "echo '#include <rdma/rdma_cma.h>' | cpp -H -o /dev/null 2>/dev/null", shell=True)
    if ret_code != 0:
        import warnings
        warnings.warn("\n\n No RDMA header file detected. Will disable RDMA for compilation! \n\n")
    return ret_code == 0


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


def test_compile(build_ext, name, code, libraries=None, include_dirs=None, library_dirs=None,
                 macros=None, extra_compile_preargs=None, extra_link_preargs=None):
    test_compile_dir = os.path.join(build_ext.build_temp, 'test_compile')
    if not os.path.exists(test_compile_dir):
        os.makedirs(test_compile_dir)

    source_file = os.path.join(test_compile_dir, '%s.cc' % name)
    with open(source_file, 'w') as f:
        f.write(code)

    compiler = build_ext.compiler
    [object_file] = compiler.object_filenames([source_file])
    shared_object_file = compiler.shared_object_filename(
        name, output_dir=test_compile_dir)

    compiler.compile([source_file], extra_preargs=extra_compile_preargs,
                     include_dirs=include_dirs, macros=macros)
    compiler.link_shared_object(
        [object_file], shared_object_file, libraries=libraries, library_dirs=library_dirs,
        extra_preargs=extra_link_preargs)

    return shared_object_file


def get_cpp_flags(build_ext):
    last_err = None
    default_flags = ['-fPIC', '-Ofast', '-Wall', '-shared', '-mno-avx512f']
    flags_to_try = [default_flags]
    for cpp_flags in flags_to_try:
        try:
            test_compile(build_ext, 'test_cpp_flags', extra_compile_preargs=cpp_flags,
                         code=textwrap.dedent('''\
                    #include <unordered_map>
                    void test() {
                    }
                    '''))

            return cpp_flags
        except (CompileError, LinkError):
            last_err = 'Unable to determine C++ compilation flags (see error above).'
        except Exception:
            last_err = 'Unable to determine C++ compilation flags.  ' \
                       'Last error:\n\n%s' % traceback.format_exc()

    raise DistutilsPlatformError(last_err)

def get_cuda_dirs(build_ext, cpp_flags):
    cuda_include_dirs = []
    cuda_lib_dirs = []

    cuda_home = os.environ.get('BYTEPS_CUDA_HOME')
    if cuda_home:
        cuda_include_dirs += ['%s/include' % cuda_home]
        cuda_lib_dirs += ['%s/lib' % cuda_home, '%s/lib64' % cuda_home]

    cuda_include = os.environ.get('BYTEPS_CUDA_INCLUDE')
    if cuda_include:
        cuda_include_dirs += [cuda_include]

    cuda_lib = os.environ.get('BYTEPS_CUDA_LIB')
    if cuda_lib:
        cuda_lib_dirs += [cuda_lib]

    if not cuda_include_dirs and not cuda_lib_dirs:
        # default to /usr/local/cuda
        cuda_include_dirs += ['/usr/local/cuda/include']
        cuda_lib_dirs += ['/usr/local/cuda/lib', '/usr/local/cuda/lib64']

    try:
        test_compile(build_ext, 'test_cuda', libraries=['cudart'], include_dirs=cuda_include_dirs,
                     library_dirs=cuda_lib_dirs, extra_compile_preargs=cpp_flags,
                     code=textwrap.dedent('''\
            #include <cuda_runtime.h>
            void test() {
                cudaSetDevice(0);
            }
            '''))
    except (CompileError, LinkError):
        raise DistutilsPlatformError(
            'CUDA library was not found (see error above).\n'
            'Please specify correct CUDA location with the BYTEPS_CUDA_HOME '
            'environment variable or combination of BYTEPS_CUDA_INCLUDE and '
            'BYTEPS_CUDA_LIB environment variables.\n\n'
            'BYTEPS_CUDA_HOME - path where CUDA include and lib directories can be found\n'
            'BYTEPS_CUDA_INCLUDE - path to CUDA include directory\n'
            'BYTEPS_CUDA_LIB - path to CUDA lib directory')

    return cuda_include_dirs, cuda_lib_dirs

def get_nccl_vals():
    nccl_include_dirs = []
    nccl_lib_dirs = []
    nccl_libs = []

    nccl_home = os.environ.get('BYTEPS_NCCL_HOME', '/usr/local/nccl')
    if nccl_home:
        nccl_include_dirs += ['%s/include' % nccl_home]
        nccl_lib_dirs += ['%s/lib' % nccl_home, '%s/lib64' % nccl_home]

    nccl_link_mode = os.environ.get('BYTEPS_NCCL_LINK', 'SHARED')
    if nccl_link_mode.upper() == 'SHARED':
        nccl_libs += ['nccl']
    else:
        nccl_libs += ['nccl_static']

    return nccl_include_dirs, nccl_lib_dirs, nccl_libs


def get_link_flags(build_ext):
    last_err = None
    libtool_flags = []
    ld_flags = []
    flags_to_try = [libtool_flags, ld_flags]
    for link_flags in flags_to_try:
        try:
            test_compile(build_ext, 'test_link_flags', extra_link_preargs=link_flags,
                         code=textwrap.dedent('''\
                    void test() {
                    }
                    '''))

            return link_flags
        except (CompileError, LinkError):
            last_err = 'Unable to determine C++ link flags (see error above).'
        except Exception:
            last_err = 'Unable to determine C++ link flags.  ' \
                       'Last error:\n\n%s' % traceback.format_exc()

    raise DistutilsPlatformError(last_err)


def build_server(build_ext, options):
    server_lib.define_macros = options['MACROS']
    server_lib.include_dirs = options['INCLUDES']
    server_lib.sources = options['SOURCES']
    server_lib.extra_compile_args = options['COMPILE_FLAGS']+\
                     ['-DBYTEPS_BUILDING_SERVER']
    server_lib.extra_link_args = options['LINK_FLAGS']
    server_lib.library_dirs = options['LIBRARY_DIRS']
    server_lib.extra_objects = options['EXTRA_OBJECTS']
    build_ext.build_extension(server_lib)


def get_common_options(build_ext):
    cpp_flags = get_cpp_flags(build_ext)
    link_flags = get_link_flags(build_ext)
    print('link_flags:', link_flags)

    MACROS = [('EIGEN_MPL2_ONLY', 1)]
    SOURCES = ['deep_inc/server/server.cc',
               'deep_inc/common/cpu_reducer.cc',
               'deep_inc/common/common.cc',
               'deep_inc/common/logging.cc',
               'deep_inc/common/communicator.cc',
               'deep_inc/common/global.cc',
               'deep_inc/common/nccl_manager.cc',
               'deep_inc/common/ready_table.cc',
               'deep_inc/common/scheduled_queue.cc',
               'deep_inc/common/shared_memory.cc',]
    COMPILE_FLAGS = cpp_flags
    LINK_FLAGS = link_flags
    INCLUDES = ['ps-lite/include']
    LIBRARY_DIRS = []
    LIBRARIES = ['ps']

    EXTRA_OBJECTS = ['ps-lite/build/libps.a',
                     'ps-lite/deps/lib/libzmq.a']
    
    nccl_include_dirs, nccl_lib_dirs, nccl_libs = get_nccl_vals()
    INCLUDES += nccl_include_dirs
    LIBRARY_DIRS += nccl_lib_dirs
    LIBRARIES += nccl_libs
    # RDMA and NUMA libs
    LIBRARIES += ['numa', 'cudart']
    

    # auto-detect rdma
    if has_rdma_header():
        LIBRARIES += ['rdmacm', 'ibverbs', 'rt']
    if use_ucx():
        LIBRARIES += ['ucp', 'uct', 'ucs', 'ucm']
        ucx_home = get_ucx_home()
        if ucx_home:
            INCLUDES += [f'{ucx_home}/include']
            LIBRARY_DIRS += [f'{ucx_home}/lib']

    return dict(MACROS=MACROS,
                INCLUDES=INCLUDES,
                SOURCES=SOURCES,
                COMPILE_FLAGS=COMPILE_FLAGS,
                LINK_FLAGS=LINK_FLAGS,
                LIBRARY_DIRS=LIBRARY_DIRS,
                LIBRARIES=LIBRARIES,
                EXTRA_OBJECTS=EXTRA_OBJECTS)


# run the customize_compiler
class custom_build_ext(build_ext):
    def build_extensions(self):
        options = get_common_options(self)
        try:
            build_server(self, options)
        except:
            raise DistutilsSetupError('An ERROR occured while building the server module.\n\n'
                                      '%s' % traceback.format_exc())


print("find_packages(): ", find_packages())
setup(
    name='DeepINC',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[

    ],
    cmdclass={
        'build_ext': custom_build_ext,
    },
    ext_modules=extensions_to_build,
    entry_points={
        'console_scripts': [

        ],
    },
)
