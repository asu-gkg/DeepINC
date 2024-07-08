# Install
```
sudo apt-get install libprotobuf-dev protobuf-compiler

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-5
sudo apt-get install -y nvidia-driver-555-open
sudo apt-get install -y cuda-drivers-555


git clone https://github.com/asu-gkg/DeepINC.git
conda activate base

git clone https://github.com/NVIDIA/nccl.git
cd nccl && make -j src.build
export BYTEPS_NCCL_HOME=/path/to/nccl

cd ps-lite && make -j
python3 setup.py build_ext --inplace
export LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:$LD_LIBRARY_PATH
```

# Run server
``` 
conda activate base
export DMLC_NUM_WORKER=2
export DMLC_NUM_SERVER=1
export DMLC_ROLE=server
export DMLC_PS_ROOT_URI=10.4.173.253
export DMLC_PS_ROOT_PORT=12345
python3 -c "import deep_inc.server"
```

# Clean
``` 
rm -rf launcher/sshlog/
sudo rm -rf build/ dist/ *.egg-info
```