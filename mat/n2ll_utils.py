import os
import subprocess as sp
# requires 'python-crontab' package to be installed
from crontab import CronTab

from mat.utils import linux_is_rpi

AG_N2LL_CMD_BYE = 'n2ll_bye'
AG_N2LL_CMD_WHO = 'n2ll_who'
AG_N2LL_CMD_QUERY = 'n2ll_query'
AG_N2LL_CMD_ROUTE = 'n2ll_route'
AG_N2LL_CMD_UNROUTE = 'n2ll_unroute'
AG_N2LL_CMD_BLED = 'n2ll_bled'
AG_N2LL_CMD_INSTALL_DDH = 'n2ll_install_ddh'
AG_N2LL_CMD_KILL_DDH = 'n2ll_uninstall_ddh'
AG_N2LL_CMD_VIEW_DDH = 'n2ll_view_ddh'
AG_N2LL_ANS_BYE = 'bye you by N2LL'
AG_N2LL_ANS_ROUTE_OK_FULL = 'ngrok routed in mac {} port {} url {}'
AG_N2LL_ANS_ROUTE_OK = 'ngrok routed in mac {}'
AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS = 'error: few permissions to rm ngrok'
AG_N2LL_ANS_ROUTE_ERR_ALREADY = 'error: ngrok not grep at {}, maybe runs somewhere else?'
AG_N2LL_ANS_NOT_FOR_US = 'cmd not for us'


def get_ngrok_bin_name() -> str:
    _s = os.uname().nodename
    _m = os.uname().machine
    if _m == 'armv7l':
        return 'ngrok_rpi'
    if _s == 'rasberrypi' or _s == 'rpi':
        return 'ngrok_rpi'
    return 'ngrok'


def check_ngrok_can_be_run():
    name = get_ngrok_bin_name()
    cmd = '{} -h'.format(name)
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        print('{} found'.format(name))
        return True
    print('maybe you need to move ngrok to /usr/bin ?')
    if linux_is_rpi():
        print('also, maybe you meant ngrok_rpi ?')


def create_empty_crontab_file_for_ddh():
    """ empties and create a new system-wide crontab file """
    ct = CronTab(user='root')
    ct.write('/etc/crontab')


def create_populated_crontab_file_for_ddh():
    """ writes new populated system-wide crontab file """
    ct = CronTab(user='root')
    job = ct.new(command='/home/pi/li/ddh/ddh_run.sh', comment='launch DDH')
    job.minute.every(2)
    ct.write('/etc/crontab')


def does_cron_job_exists_by_comment(file_name: str, comm: str):
    """ checks if job w/ comment exists in crontab file 'f' """
    assert file_name
    ct = CronTab(user='root', tabfile=file_name)
    iter_job = ct.find_comment(comm)
    rv = len(list(iter_job))
    s = 'job w/ comment {} present at file {}? {} '
    print(s.format(comm, file_name, bool(rv)))
    return bool(rv)

