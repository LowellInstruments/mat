import os
import subprocess as sp
# requires 'python-crontab' package to be installed
import pika
from crontab import CronTab

from mat.utils import linux_is_rpi

AG_N2LL_CMD_BYE = 'n2ll_bye'
AG_N2LL_CMD_WHO = 'n2ll_who'
AG_N2LL_CMD_QUERY = 'n2ll_query'
AG_N2LL_CMD_ROUTE = 'n2ll_route'
AG_N2LL_CMD_UNROUTE = 'n2ll_unroute'
AG_N2LL_CMD_NGROK_VIEW = 'n2ll_ngrok_view'
AG_N2LL_CMD_BLED = 'n2ll_bled'
AG_N2LL_CMD_INSTALL_DDH = 'n2ll_install_ddh'
AG_N2LL_CMD_KILL_DDH = 'n2ll_uninstall_ddh'
AG_N2LL_CMD_VIEW_DDH = 'n2ll_view_ddh'
AG_N2LL_CMD_XR_START = 'n2ll_xr_start'
AG_N2LL_CMD_XR_VIEW = 'n2ll_xr_view'
AG_N2LL_CMD_XR_KILL = 'n2ll_xr_end'
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


def _url_n2ll():
    """ build and return the N2LL url """

    # todo: change this test url to a production one
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


def _mq_get_ch():
    """ build and return the N2LL channel (needs url) """

    url = _url_n2ll()
    _pars = pika.URLParameters(url)
    _pars.socket_timeout = 3
    _conn = pika.BlockingConnection(_pars)
    return _conn.channel()


def mq_exchange_for_slaves():
    """ build and return the N2LL slave exchange (needs channel) """

    _ch = _mq_get_ch()
    _ch.exchange_declare(exchange='li_slaves', exchange_type='fanout')
    return _ch


def mq_exchange_for_masters():
    """ build and return the N2LL master exchange (needs channel) """

    _ch = _mq_get_ch()
    _ch.exchange_declare(exchange='li_masters', exchange_type='fanout')
    return _ch
