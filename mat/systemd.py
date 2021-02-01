import os
import subprocess as sp


# tested to work for both 'name' / 'name.service'
# ex: 'bluetooth' / 'bluetooth.service',
# ex: 'vncserver-x11-serviced' / 'vncserver-x11-serviced.service'


def systemd_list_all_services_running():
    # running: currently executed, may be enabled or not
    s = 'systemctl | grep running'
    rv = sp.run(s, shell=True, stdout=sp.PIPE)
    return rv.stdout


def systemd_list_all_services_enabled():
    # enabled: will start on next boot, may be currently running or not
    s = 'systemctl list-unit-files | grep enabled'
    rv = sp.run(s, shell=True, stdout=sp.PIPE)
    return rv.stdout


def systemd_is_this_service_active(name: str) -> bool:
    s = 'systemctl is-active --quiet {}'
    return os.system(s.format(name)) == 0


def systemd_is_this_service_enabled(name: str) -> bool:
    s = 'systemctl is-enabled --quiet {}'
    return os.system(s.format(name)) == 0


def systemd_do_operation_on_service(op: str, some: str):
    assert op in ('start', 'stop')
    s = 'systemctl {} {}.service'.format(op, some)
    rv = sp.run([s], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return rv.returncode == 0
