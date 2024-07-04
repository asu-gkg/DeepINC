import os
import subprocess
from threading import Thread


def get_hosts_from_file(filename):
    with open(filename) as f:
        tmp = f.readlines()
    assert len(tmp) > 0
    hosts = []
    for h in tmp:
        if len(h.strip()) > 0:
            # parse addresses of the form ip:port
            h = h.strip()
            i = h.find(":")
            p = "22"
            if i != -1:
                p = h[i+1:]
                h = h[:i]
            # hosts now contain the pair ip, port
            hosts.append((h, p))
    return hosts


def start_ssh(prog, node, port, username, fname):
    def run(prog):
        subprocess.check_call(prog, shell=True)

    dirname = 'sshlog'
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    pname = dirname + '/' + fname
    if username is not None:
        prog = 'ssh -o StrictHostKeyChecking=no ' + ' -l ' + username \
               + ' ' + node + ' -p ' + port + ' \'' + prog + '\'' \
               + ' > ' + pname + '.stdout' + ' 2>' + pname + '.stderr&'
    else:
        prog = 'ssh -o StrictHostKeyChecking=no ' + node + ' -p ' + port + ' \'' + prog + '\'' \
               + ' > ' + pname + '.stdout' + ' 2>' + pname + '.stderr&'

    thread = Thread(target=run, args=(prog,))
    thread.setDaemon(True)
    thread.start()
    return thread


def get_env(envs_map):
    envs = []
    # get system envs
    keys = ['OMP_NUM_THREADS', 'KMP_AFFINITY']
    for k in keys:
        v = os.getenv(k)
        if v is not None:
            envs.append('export ' + k + '=' + v + ';')
    # get ass_envs
    for k, v in envs_map.items():
        envs.append('export ' + str(k) + '=' + str(v) + ';')
    return (' '.join(envs))