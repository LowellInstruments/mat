import subprocess as sp
import os


def linux_app_write_pid_to_tmp(name):
    if not name.endswith('.pid'):
        name += '.pid'
    if not name.startswith('/tmp/'):
        name = '/tmp/' + name
    path = name
    pid = str(os.getpid())
    f = open(path, 'w')
    f.write(pid)
    f.close()


def linux_is_process_running(name) -> bool:
    cmd = f'ps -aux | grep {name} | grep -v grep'
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return rv.returncode == 0


def linux_is_process_running_strict(name) -> bool:
    cmd = f'ps -aux | grep -w {name} | grep -v grep'
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return rv.returncode == 0
