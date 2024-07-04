# Setup
In each hosts, do
``` 
ssh-copy-id -i ~/.ssh/id_rsa.pub your_username@remote_host
```

# Usuage

``` 
python3 dist_launcher.py -WH ../config/workers -SH ../config/servers --scheduler-ip 10.4.173.253 --scheduler-port 12345 --username asu --command "echo this is \$ROLE; python3 DeepINC/launcher/launch.py YOUR_COMMAND"
```