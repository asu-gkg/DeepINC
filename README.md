# Install
```
cd ps-lite && make -j
python3 setup.py build_ext --inplace
python3 setup.py install
```

# Run server
``` 
python3 -c "import deep_inc.server"
```

# Clean
``` 
rm -rf launcher/sshlog/
sudo rm -rf build/ dist/ *.egg-info
```