import sys
import os
import subprocess
import threading
from utils import PropagatingThread

COMMON_REQUIRED_ENVS = ["DMLC_ROLE", "DMLC_NUM_WORKER", "DMLC_NUM_SERVER",
                        "DMLC_PS_ROOT_URI", "DMLC_PS_ROOT_PORT"]

WORKER_REQUIRED_ENVS = ["DMLC_WORKER_ID"]



# for launcher to check env
def check_env():
    assert "DMLC_ROLE" in os.environ and \
           os.environ["DMLC_ROLE"].lower() in ["worker", "server", "scheduler"]
    required_envs = COMMON_REQUIRED_ENVS
    if os.environ["DMLC_ROLE"] == "worker":
        assert "DMLC_NUM_WORKER" in os.environ
        num_worker = int(os.environ["DMLC_NUM_WORKER"])
        assert num_worker >= 1
        if num_worker == 1:
            required_envs = []
        required_envs += WORKER_REQUIRED_ENVS
    for env in required_envs:
        if env not in os.environ:
            print("The env " + env + " is missing")
            os._exit(0)

def launch_deep_inc():
    print("DeepINC launching " + os.environ["DMLC_ROLE"])
    sys.stdout.flush()
    check_env()
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["UCX_HANDLE_ERRORS"] = os.getenv("UCX_HANDLE_ERRORS", "none")
    if os.environ["ROLE"] == "worker":
        if "NVIDIA_VISIBLE_DEVICES" in os.environ:
            local_size = len(os.environ["NVIDIA_VISIBLE_DEVICES"].split(","))
        else:
            local_size = 1
        t = [None] * local_size

        bind_to_cores = os.getenv("NUMA_ON", "1") == "1"
        if bind_to_cores:
            user_override = os.getenv("VISIBLE_CPU_CORES", "").strip()
            if user_override:
                allocations = parse_num_range(user_override)
            else:
                allocations = allocate_cpu(local_size)

        for i in range(local_size):
            command = ' '.join(sys.argv[1:])
            if bind_to_cores:
                t[i] = PropagatingThread(idx=i, callback=done_callback,
                    target=worker,
                    args=[i, local_size, command, allocations[i]])
            else:
                t[i] = PropagatingThread(idx=i, callback=done_callback,
                    target=worker, args=[i, local_size, command])
            t[i].daemon = True
            t[i].start()

        join_threads(t)

    elif os.environ.get("FORCE_DISTRIBUTED", "") == "1" or \
         int(os.environ.get("DMLC_NUM_WORKER", "1")) > 1:
        command = "echo 'launch server'"
        if int(os.getenv("ENABLE_GDB", 0)):
            command = "gdb -ex 'run' -ex 'bt' -batch --args " + command
        print("Command: %s\n" % command, flush=True)
        my_env = os.environ.copy()
        subprocess.check_call(command, env=my_env,
                              stdout=sys.stdout, stderr=sys.stderr, shell=True)


if __name__ == "__main__":
    launch_deep_inc()
