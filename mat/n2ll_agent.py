import os
import subprocess as sp
import threading
import time
import pika
from getmac import get_mac_address
from pika.exceptions import AMQPError

from mat.linux import linux_is_rpi
from mat.n2lx_utils import (AG_N2LL_ANS_BYE, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS,
                            AG_N2LL_ANS_ROUTE_ERR_ALREADY, AG_N2LL_ANS_ROUTE_OK_FULL,
                            AG_N2LL_CMD_WHO, AG_N2LL_CMD_BYE, AG_N2LL_CMD_QUERY,
                            AG_N2LL_CMD_ROUTE, AG_N2LL_CMD_UNROUTE,
                            AG_N2LL_ANS_NOT_FOR_US, AG_N2LL_ANS_ROUTE_NOK, get_ngrok_bin_name, check_ngrok_can_be_run,
                            AG_N2LL_CMD_UNINSTALL_DDH, AG_N2LL_CMD_INSTALL_DDH)
from mat.utils import is_program_running, create_empty_cron_file_for_ddh


def _p(s):
    print(s, flush=True)


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
    mac = macs[0]
    is_ddh_running = int(is_program_running('ddh/main.py'))
    is_ngrok_running = int(is_program_running(get_ngrok_bin_name()))
    s = '{} DDH {} / ngrok {}'
    return 0, s.format(mac, is_ddh_running, is_ngrok_running)


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


def _cmd_ddh_rpi(_, macs):
    mac = macs[0]
    if not linux_is_rpi():
        return 0, '{} is not a raspberry'.format(mac)

    # todo: finish this function
    # 1st, call _cmd_unddh_rpi()
    _cmd_unddh_rpi(_, macs)
    # 2nd, git clone ddh
    cmd = 'mkdir /home/pi/ddh; cd /home/pi/ddh;'
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    cmd = 'git clone...'
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # 3rd, create crontab
    return 0, 'installed DDH on {}'.format(mac)


def _cmd_unddh_rpi(_, macs):
    mac = macs[0]
    if not linux_is_rpi():
        return 0, '{} is not a raspberry'.format(mac)

    # 1st, disable any crontab controlling DDH
    create_empty_cron_file_for_ddh()
    # 2nd, killall DDH
    # todo: improve this killing
    cmd = 'killall python3'
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # 3rd, rm -rf ddh
    cmd = 'rm -rf /home/pi/ddh'
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return 0, 'uninstalled DDH on {}'.format(mac)


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
        AG_N2LL_CMD_INSTALL_DDH: _cmd_ddh_rpi,
        AG_N2LL_CMD_UNINSTALL_DDH: _cmd_unddh_rpi
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

