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
import re

server_lib = Extension('deep_inc.server.c_lib', [])
pytorch_lib = Extension('byteps.torch.c_lib', [])

extensions_to_build = [server_lib, pytorch_lib]

os.environ["CC"] = "gcc"
os.environ["CXX"] = "g++"

def has_rdma_header():
    ret_code = subprocess.call(
        "echo '#include <rdma/rdma_cma.h>' | cpp -H -o /dev/null 2>/dev/null", shell=True)
    if ret_code != 0:
        import warnings
        warnings.warn("\n\n No RDMA header file detected. Will disable RDMA for compilation! \n\n")
    return ret_code == 0


def check_macro(macros, key):
    return any(k == key and v for k, v in macros)

def set_macro(macros, key, new_value):
    if any(k == key for k, _ in macros):
        return [(k, new_value if k == key else v) for k, v in macros]
    else:
        return macros + [(key, new_value)]


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


def parse_version(version_str):
    if "dev" in version_str:
        return 9999999999
    m = re.match('^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?', version_str)
    if m is None:
        return None

    # turn version string to long integer
    version = int(m.group(1)) * 10 ** 9
    if m.group(2) is not None:
        version += int(m.group(2)) * 10 ** 6
    if m.group(3) is not None:
        version += int(m.group(3)) * 10 ** 3
    if m.group(4) is not None:
        version += int(m.group(4))
    return version

def get_cpp_flags(build_ext):
    last_err = None
    default_flags = ['-std=c++17', '-fPIC', '-Ofast', '-frtti', '-Wall', '-shared', '-mno-avx512f', '-lcudart', '-lnuma', '-lnccl']
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

    nccl_home = os.environ.get('BYTEPS_NCCL_HOME', 'nccl/build')
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
    server_lib.libraries = options['LIBRARIES']
    build_ext.build_extension(server_lib)

def check_torch_version():
    try:
        import torch
        if torch.__version__ < '1.0.1':
            raise DistutilsPlatformError(
                'Your torch version %s is outdated.  '
                'BytePS requires torch>=1.0.1' % torch.__version__)
    except ImportError:
            print('import torch failed, is it installed?\n\n%s' %
                  traceback.format_exc())

    # parse version
    version = parse_version(torch.__version__)
    if version is None:
        raise DistutilsPlatformError(
            'Unable to determine PyTorch version from the version string \'%s\'' % torch.__version__)
    return version

def is_torch_cuda(build_ext, include_dirs, extra_compile_args):
    try:
        from torch.utils.cpp_extension import include_paths
        test_compile(build_ext, 'test_torch_cuda', include_dirs=include_dirs + include_paths(cuda=True),
                     extra_compile_preargs=extra_compile_args, code=textwrap.dedent('''\
            #include <ATen/cuda/CUDAContext.h>
            #include <ATen/cuda/CUDAEvent.h>
            void test() {
            }
            '''))
        return True
    except (CompileError, LinkError, EnvironmentError):
        print('INFO: Above error indicates that this PyTorch installation does not support CUDA.')
        return False

def build_torch_extension(build_ext, options, torch_version):
    pytorch_compile_flags = ["-std=c++17" if flag == "-std=c++11" 
                             else flag for flag in options['COMPILE_FLAGS']]
    have_cuda = is_torch_cuda(build_ext, include_dirs=options['INCLUDES'],
                              extra_compile_args=pytorch_compile_flags)
    if not have_cuda and check_macro(options['MACROS'], 'HAVE_CUDA'):
        raise DistutilsPlatformError(
            'byteps build with GPU support was requested, but this PyTorch '
            'installation does not support CUDA.')

    # Update HAVE_CUDA to mean that PyTorch supports CUDA.
    updated_macros = set_macro(
        options['MACROS'], 'HAVE_CUDA', str(int(have_cuda)))

    # Export TORCH_VERSION equal to our representation of torch.__version__. Internally it's
    # used for backwards compatibility checks.
    updated_macros = set_macro(
       updated_macros, 'TORCH_VERSION', str(torch_version))

    # Always set _GLIBCXX_USE_CXX11_ABI, since PyTorch can only detect whether it was set to 1.
    import torch
    updated_macros = set_macro(updated_macros, '_GLIBCXX_USE_CXX11_ABI',
                               str(int(torch.compiled_with_cxx11_abi())))

    # PyTorch requires -DTORCH_API_INCLUDE_EXTENSION_H
    updated_macros = set_macro(
        updated_macros, 'TORCH_API_INCLUDE_EXTENSION_H', '1')

    if have_cuda:
        from torch.utils.cpp_extension import CUDAExtension as TorchExtension
    else:
        # CUDAExtension fails with `ld: library not found for -lcudart` if CUDA is not present
        from torch.utils.cpp_extension import CppExtension as TorchExtension

    ext = TorchExtension(pytorch_lib.name,
                         define_macros=updated_macros,
                         include_dirs=options['INCLUDES'],
                         sources=options['SOURCES'] + ['byteps/torch/ops.cc',
                                                       'byteps/torch/ready_event.cc',
                                                       'byteps/torch/cuda_util.cc',
                                                       'byteps/torch/adapter.cc',
                                                       'byteps/torch/handle_manager.cc'],
                         extra_compile_args=pytorch_compile_flags,
                         extra_link_args=options['LINK_FLAGS'],
                         extra_objects=options['EXTRA_OBJECTS'],
                         library_dirs=options['LIBRARY_DIRS'],
                         libraries=options['LIBRARIES'])

    # Patch an existing pytorch_lib extension object.
    for k, v in ext.__dict__.items():
        pytorch_lib.__dict__[k] = v
    build_ext.build_extension(pytorch_lib)


def get_common_options(build_ext):
    cpp_flags = get_cpp_flags(build_ext)
    link_flags = get_link_flags(build_ext)
    print('link_flags:', link_flags)

    MACROS = [('EIGEN_MPL2_ONLY', 1)]
    SOURCES = ['deep_inc/server/server.cc',
               'deep_inc/common/operations.cc',
               'deep_inc/common/cpu_reducer.cc',
               'deep_inc/common/common.cc',
               'deep_inc/common/logging.cc',
               'deep_inc/common/communicator.cc',
               'deep_inc/common/global.cc',
               'deep_inc/common/nccl_manager.cc',
               'deep_inc/common/ready_table.cc',
               'deep_inc/common/scheduled_queue.cc',
               'deep_inc/common/shared_memory.cc',          
               'deep_inc/common/core_loops.cc',
                'deep_inc/common/compressor/compressor_registry.cc',
               'deep_inc/common/compressor/error_feedback.cc',
               'deep_inc/common/compressor/momentum.cc',
               'deep_inc/common/compressor/impl/dithering.cc',
               'deep_inc/common/compressor/impl/onebit.cc',
               'deep_inc/common/compressor/impl/randomk.cc',
               'deep_inc/common/compressor/impl/topk.cc',
               'deep_inc/common/compressor/impl/vanilla_error_feedback.cc',
               'deep_inc/common/compressor/impl/nesterov_momentum.cc'] 
    COMPILE_FLAGS = cpp_flags
    LINK_FLAGS = link_flags
    INCLUDES = ['ps-lite/include']
    LIBRARY_DIRS = []
    LIBRARIES = []

    EXTRA_OBJECTS = ['ps-lite/build/libps.a',
                     'ps-lite/deps/lib/libzmq.a', 
                     'ps-lite/deps/lib/libprotobuf.a']
    
    nccl_include_dirs, nccl_lib_dirs, nccl_libs = get_nccl_vals()
    print("NCCL_INCLUDES: ", nccl_include_dirs)
    INCLUDES += nccl_include_dirs
    LIBRARY_DIRS += nccl_lib_dirs
    LIBRARIES += nccl_libs
    # RDMA and NUMA libs
    LIBRARIES += ['numa']
    LIBRARIES += ['cudart', 'cuda', 'cublas']

    cuda_include_dirs, cuda_lib_dirs = get_cuda_dirs(
        build_ext, COMPILE_FLAGS)
    
    MACROS += [('HAVE_CUDA', '1')]
    INCLUDES += cuda_include_dirs
    LIBRARY_DIRS += cuda_lib_dirs

    print("CUDA_INCLUDES: ", cuda_include_dirs)
    print("CUDA_LIBS: ", cuda_lib_dirs)

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
        # try:
        #     build_server(self, options)
        # except:
        #     raise DistutilsSetupError('An ERROR occured while building the server module.\n\n'
        #                               '%s' % traceback.format_exc())
        
        import torch
        try:
            torch_version = check_torch_version()
            build_torch_extension(self, options, torch_version)
        except:
            pass
        

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