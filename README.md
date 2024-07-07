# Install
```
sudo apt-get install libprotobuf-dev protobuf-compiler
sudo apt install nvidia-cuda-toolkit
cd ps-lite && make -j
python3 setup.py build_ext --inplace
```

# Run server
``` 
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