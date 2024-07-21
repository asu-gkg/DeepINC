# Install
```
sudo apt-get install libprotobuf-dev protobuf-compiler
sudo apt-get install libnuma-dev
conda install protobuf

# sudo dpkg -i cuda-repo-<distro>_<version>_<architecture>.deb
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
dpkg -l | grep cuda-keyring
sudo apt-get update
sudo apt-get -y install cuda-toolkit
sudo apt-get install -y nvidia-driver-555-open
sudo apt-get install -y cuda-drivers-555

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cudnn
sudo apt-get -y install cudnn-cuda-12


git clone https://github.com/asu-gkg/DeepINC.git
conda activate base

git clone https://github.com/NVIDIA/nccl.git
cd nccl && make -j src.build
export BYTEPS_NCCL_HOME=/path/to/nccl

cd ps-lite && make -j

conda activate base
export BYTEPS_NCCL_HOME=/home/asu/DeepINC/nccl/build
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/cuda/targets/x86_64-linux/lib/stubs:$LD_LIBRARY_PATH
export BYTEPS_CUDA_HOME=/usr/local/cuda
python3 setup.py build_ext --inplace


```

# Docker
```
cd docker
sudo docker build -t deepinc_image .
 
docker run --gpus all --network host --name deepinc_server_container -it horovod/horovod
sudo docker start deepinc_server_container
docker exec -it deepinc_server_container /bin/bash


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