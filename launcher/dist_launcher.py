import logging
import argparse
from utils import get_hosts_from_file, start_ssh, get_env
import sys
import signal


def submit(args):
    worker_hosts = get_hosts_from_file(args.worker_hostfile)
    server_hosts = get_hosts_from_file(args.server_hostfile)
    num_worker = len(worker_hosts)
    num_server = len(server_hosts)
    assert num_worker >= 1
    assert num_server >= 1
    print('Launch %d workers and %d servers' % (num_worker, num_server))

    print('worker_hosts: %s' % worker_hosts)
    print('server_hosts: %s' % server_hosts)

    pass_envs = {}
    pass_envs['NUM_WORKER'] = str(num_worker)
    pass_envs['NUM_SERVER'] = str(num_server)
    pass_envs['PS_ROOT_URI'] = str(args.scheduler_ip)
    pass_envs['PS_ROOT_PORT'] = str(args.scheduler_port)

    username = ''
    if args.username is not None:
        username = args.username

    print('args.command: %s' % args.command)
    threads = []
    for (node, port) in [(args.scheduler_ip, args.scheduler_ssh_port)]:
        name = 'scheduler'
        pass_envs['ROLE'] = name
        prog = get_env(pass_envs) + (' '.join(args.command))
        threads.append(start_ssh(prog, node, port, username, name))

    for t in threads:
        t.join()

def signal_handler(signal, frame):
    logging.info('Stop launcher')
    sys.exit(0)

if __name__ == '__main__':
    fmt = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(format=fmt, level=logging.INFO)

    logging.info('---Start---')
    parser = argparse.ArgumentParser(description='Launch a distributed training job for BytePS')
    parser.add_argument('-WH', '--worker-hostfile', required=True, type=str,
                        help = 'the hostfile of worker machines which will run the job.')
    parser.add_argument('-SH', '--server-hostfile', required=True, type=str,
                        help = 'the hostfile of server machines which will run the job.')
    parser.add_argument('--scheduler-ip', required=True, type=str,
                        help = 'the ip address of the scheduler')
    parser.add_argument('--scheduler-port', required=True, type=int,
                        help = 'the port of the scheduler')
    parser.add_argument('--username', type=str,
                        help = 'the username for ssh')
    parser.add_argument('--scheduler-ssh-port', type=str, default='22',
                        help = 'the ssh port of the scheduler')
    parser.add_argument('--command', nargs='+',
                        help = 'command for launching the program')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    # check necessary args
    assert args.worker_hostfile
    assert args.server_hostfile
    assert args.scheduler_ip
    assert args.scheduler_port

    submit(args)