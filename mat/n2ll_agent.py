import os
import subprocess as sp
import threading
import time
import pika
from getmac import get_mac_address
from pika.exceptions import AMQPError
from mat.n2lx_utils import (AG_N2LL_ANS_BYE, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS,
                            AG_N2LL_ANS_ROUTE_ERR_ALREADY, AG_N2LL_ANS_ROUTE_OK_FULL,
                            AG_N2LL_CMD_WHO, AG_N2LL_CMD_BYE, AG_N2LL_CMD_QUERY,
                            AG_N2LL_CMD_ROUTE, AG_N2LL_CMD_UNROUTE,
                            AG_N2LL_ANS_NOT_FOR_US, AG_N2LL_ANS_ROUTE_NOK, get_ngrok_bin_name, check_ngrok_can_be_run)
# requires 'python-crontab' package to be installed
# from crontab import CronTab


def _p(s):
    print(s, flush=True)


# todo: move this to MAT systemd utils.py
# import os
# import subprocess as sp
# import pprint
#
#
# def is_service_active(name: str):
#     # just name, not name.service
#     s = 'systemctl is-active --quiet {}'.format(name)
#     rv = sp.run(s, shell=True)
#     print('service active {} ? {}'.format(name, rv.returncode == 0))
#     return rv.returncode == 0
#
#
# def is_service_enabled(name: str):
#     # just name, not name.service
#     s = 'systemctl is-enabled --quiet {}'.format(name)
#     rv = sp.run(s, shell=True)
#     print('service enabled {} ? {}'.format(name, rv.returncode == 0))
#     return rv.returncode == 0
#
#
# def list_services_running():
#     # running: currently being executed, may be enabled or not
#     s = 'systemctl | grep running'
#     rv = sp.run(s, shell=True, stdout=sp.PIPE)
#     pprint.pprint(rv.stdout)
#
#
# def list_services_enabled():
#     # enabled: will start on next boot, may be currently running or not
#     s = 'systemctl list-unit-files | grep enabled'
#     rv = sp.run(s, shell=True, stdout=sp.PIPE)
#     pprint.pprint(rv.stdout)
#
# def is_program_running(name):
#     _grep = 'ps aux | grep {} | grep -v grep'.format(name)
#     rv = sp.run(_grep, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
#     return rv.returncode == 0
#
# if __name__ == '__main__':
#     is_service_active('NetworkManager')
#     is_service_active('FakeEntry')
#     is_service_enabled('NetworkManager')
#     is_service_enabled('apparmor')
#     # list_services_enabled()
#






# def does_cron_job_exists_by_comment(file_name: str, comm: str):
#     """ checks if job w/ comment exists in crontab file 'f' """
#     assert file_name
#     ct = CronTab(user='root', tabfile=file_name)
#     iter_job = ct.find_comment(comm)
#     rv = len(list(iter_job))
#     s = 'job w/ comment {} present at file {}? {} '
#     print(s.format(comm, file_name, bool(rv)))
#     return bool(rv)
#
#
# def write_cron_file(file_name: str):
#     """ writes new crontab file from scratch """
#     ct = CronTab(user='root')
#     ct.new(command='echo hello 1')
#     ct.new(command='echo hello 2', comment='helloID')
#     ct.write(file_name)
#
#
# def read_system_wide_crontab_file():
#     # constructor already calls read()
#     ct = CronTab(user='root', tabfile='/etc/crontab')
#     for line in ct.lines:
#         print(line)
#
#
# if __name__ == '__main__':
#     crontab_file_name = './me.tab'
#     write_cron_file(crontab_file_name)
#     does_cron_job_exists_by_comment(crontab_file_name, 'fakeID')
#     does_cron_job_exists_by_comment(crontab_file_name, 'helloID')
#     read_system_wide_crontab_file()


def _url_n2ll():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


def _mq_get_ch():
    url = _url_n2ll()
    _pars = pika.URLParameters(url)
    _pars.socket_timeout = 3
    _conn = pika.BlockingConnection(_pars)
    return _conn.channel()


def mq_exchange_for_slaves():
    _ch = _mq_get_ch()
    _ch.exchange_declare(exchange='li_slaves', exchange_type='fanout')
    return _ch


def mq_exchange_for_masters():
    _ch = _mq_get_ch()
    _ch.exchange_declare(exchange='li_masters', exchange_type='fanout')
    return _ch


def _cmd_who(_, macs):
    return 0, ' '.join([m for m in macs if m and m != '*'])


def _cmd_bye(_, macs):
    return 0, '{} in {}'.format(AG_N2LL_ANS_BYE, macs)


def _cmd_query(_, macs):
    name = get_ngrok_bin_name()
    _grep = 'ps aux | grep {} | grep -v grep'.format(name)
    rv = sp.run(_grep, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        return 0, 'ngrok routed at {}'.format(macs[0])
    return 1, AG_N2LL_ANS_ROUTE_NOK.format(macs[0])


def _cmd_route_ngrok(_, macs):
    # _: ['route', '4000', <mac>]
    assert len(_) == 3

    # obtain proper ngrok name and kill any current local one
    ngrok_bin = get_ngrok_bin_name()
    cmd = 'killall {}'.format(ngrok_bin)
    sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    # remove any previous ngrok log file
    log_file = '/tmp/ngrok.log'
    cmd = 'rm {}'.format(log_file)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if b'permission denied' in _rv.stderr:
        return 1, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS

    # Popen() daemons ngrok, although cannot check return code
    port = _[1]
    cmd = '{} tcp {} -log={}'.format(ngrok_bin, port, log_file)
    # _p(cmd)
    sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    # see log file, grep ngrok url
    time.sleep(2)
    cmd = 'cat {} | grep \'started tunnel\''.format(log_file)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if _rv.returncode:
        e = AG_N2LL_ANS_ROUTE_ERR_ALREADY
        return 1, e.format(macs[0])

    # grab the output of cat as ngrok url
    g = _rv.stdout
    u = g.decode().strip().split('url=')[1]
    s = AG_N2LL_ANS_ROUTE_OK_FULL.format(macs[0], port, u)
    return 0, s


def _cmd_unroute(_, macs):
    ngrok_bin = get_ngrok_bin_name()
    cmd = 'killall {}'.format(ngrok_bin)
    _rv = sp.run([cmd], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    mac = macs[0]
    return 0, 'un-routed {}'.format(mac)


def _parse_n2ll_in_cmd(s: bytes):
    # s: AG_N2LL_CMD_QUERY <mac> <port>
    if not s:
        return 1, 'error, cmd empty'

    # parse n2ll stuff
    s = s.decode().split(' ')

    # which are my own mac addresses
    _my_macs = [
                get_mac_address(interface='eth0'),
                get_mac_address(interface='wlo1'),
                get_mac_address(interface='wlan0'),
                '*']

    # remove Nones
    _my_macs = [i for i in _my_macs if i]

    # search the N2LL function
    cmd = s[0]
    fxn_map = {
        AG_N2LL_CMD_BYE: _cmd_bye,
        AG_N2LL_CMD_WHO: _cmd_who,
        AG_N2LL_CMD_QUERY: _cmd_query,
        AG_N2LL_CMD_ROUTE: _cmd_route_ngrok,
        AG_N2LL_CMD_UNROUTE: _cmd_unroute,
    }
    fxn = fxn_map[cmd]

    # is this N2LL frame for us?
    if len(s) >= 2:
        mac = s[-1]
        if mac not in _my_macs:
            return 1, '{} {}'.format(AG_N2LL_ANS_NOT_FOR_US, _my_macs)
    else:
        # commands w/o mac
        if not cmd.startswith(AG_N2LL_CMD_WHO):
            return 1, 'cmd bad number of parameters'

    # noinspection PyArgumentList
    return fxn(s, _my_macs)


class AgentN2LL(threading.Thread):
    def __init__(self, url):
        """ ClientN2LL pubs  in channel 'li_masters', subs to 'li_slaves'
            AgentN2LL (n of them) pub to 'li_slaves', sub to 'li_masters' """
        assert(check_ngrok_can_be_run())
        super().__init__()
        self.url = url
        self.ch_pub = None
        self.ch_sub = None

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_slaves()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_masters()

    @staticmethod
    def _do_i_quit(ans):
        if AG_N2LL_ANS_BYE in ans:
            # give time answer to travel back
            time.sleep(5)
            _p('quitting AG_N2LL')
            os._exit(0)

    def loop_n2ll(self):
        """ AgentN2LL spawns no hreads: receives at rx and tx back """
        _p('N2LL: listening on {}'.format(self.url.split('/')[-1]))
        while 1:
            try:
                self._sub_n_rx()
            except (Exception, AMQPError) as e:
                _p('N2LL: error rx_exc -> {}'.format(e))

    def _pub(self, _what):
        self._get_ch_pub()
        self.ch_pub.basic_publish(exchange='li_slaves', routing_key='', body=_what)
        # _p('<- N2LL: pub {}'.format(_what))
        self.ch_pub.close()

    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            # _p('-> N2LL: rx_cb {}'.format(body))
            ans = _parse_n2ll_in_cmd(body)
            # ans: (0, description) send to channel 'li_slaves'
            self._pub(ans[1])
            # maybe time to end myself
            self._do_i_quit(ans[1])

        # receive from channel 'li_masters'
        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', durable=True, exclusive=True)
        q = rv.method.queue
        self.ch_sub.queue_bind(exchange='li_masters', queue=q)
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()
