# requires 'python-crontab' package to be installed
import pika
import parse
from crontab import CronTab


AG_N2LL_CMD_BYE = 'n2ll_bye'
AG_N2LL_CMD_WHO = 'n2ll_who'
AG_N2LL_CMD_QUERY = 'n2ll_query'
AG_N2LL_CMD_ROUTE = 'n2ll_route'
AG_N2LL_CMD_UNROUTE = 'n2ll_unroute'
AG_N2LL_CMD_NGROK_VIEW = 'n2ll_ngrok_view'
AG_N2LL_CMD_BLE_SERVICE_RESTART = 'n2ll_ble_service_restart'
AG_N2LL_CMD_INSTALL_DDH = 'n2ll_install_ddh'
AG_N2LL_CMD_KILL_DDH = 'n2ll_uninstall_ddh'
AG_N2LL_CMD_DDH_VESSEL = 'n2ll_view_ddh'
AG_N2LL_CMD_XR_START = 'n2ll_xr_start'
AG_N2LL_CMD_XR_VIEW = 'n2ll_xr_view'
AG_N2LL_CMD_XR_KILL = 'n2ll_xr_end'
AG_N2LL_ANS_BYE = 'bye you by N2LL'
AG_N2LL_ANS_ROUTE_OK_FULL = 'ngrok routed in mac {} port {} url {}'
AG_N2LL_ANS_ROUTE_OK = 'ngrok routed in mac {}'
AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS = 'error: few permissions to rm ngrok'
AG_N2LL_ANS_ROUTE_ERR_ALREADY = 'error: ngrok not grep at {}, maybe runs somewhere else?'
AG_N2LL_ANS_NOT_FOR_US = 'cmd not for us'


def ddh_create_empty_crontab_file():
    """ empties and create a new system-wide crontab file """
    ct = CronTab(user='root')
    ct.write('/etc/crontab')


def ddh_create_populated_crontab_file():
    """ writes new populated system-wide crontab file """
    ct = CronTab(user='root')
    job = ct.new(command='/home/pi/li/ddh/ddh_run.sh', comment='launch DDH')
    job.minute.every(2)
    ct.write('/etc/crontab')


def ddh_grep_cron_job_by_comment_in_file(file_name: str, comm: str):
    """ checks if job w/ comment exists in crontab file 'f' """
    assert file_name
    ct = CronTab(user='root', tabfile=file_name)
    iter_job = ct.find_comment(comm)
    rv = len(list(iter_job))
    s = 'job w/ comment {} present at file {}? {} '
    print(s.format(comm, file_name, bool(rv)))
    return bool(rv)


# ################# N2LL connection and parameters ###############
def n2ll_url():
    # see all this info and the one in _mq_get_ch()
    # in rabbitMQ console AND admin pages
    _user = 'rrcjfcnm'
    _pass = 'NsbkDVluGBjRcU3j37sbMg6_FlfgpcQa'
    _vhost = _user
    _host = 'cattle.rmq2.cloudamqp.com'
    s = 'amqps://{}:{}@{}/{}'
    return s.format(_user, _pass, _host, _vhost)


def _mq_get_ch():
    """ build and return the N2LL channel (needs url) """
    _user, _pass, _host, _vhost = parse.parse('amqps://{}:{}@{}/{}', n2ll_url())
    _cred = pika.PlainCredentials(_user, _pass)
    _pars = pika.ConnectionParameters(_host, 5672, _vhost, _cred)
    _pars.socket_timeout = 3
    _conn = pika.BlockingConnection(_pars)
    return _conn.channel()
# #################################################################


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
