export BYTEPS_CUDA_HOME=/usr/local/cuda
export BYTEPS_NCCL_HOME=/home/asu/DeepINC/nccl/build

export DMLC_NUM_WORKER=2
export DMLC_NUM_SERVER=1
export DMLC_ROLE=server
export DMLC_PS_ROOT_URI=10.4.173.253
export DMLC_PS_ROOT_PORT=12345

install:
	python setup.py bdist_wheel

build:

	python3 setup.py build_ext --inplace

run:
	python3 -c "import deep_inc.server"

clean:
	python3 setup.py clean
	rm -rf build DeepINC.egg-info

