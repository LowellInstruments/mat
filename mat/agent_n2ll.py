import os
import subprocess as sp
import threading
import time
import pika
from getmac import get_mac_address
from pika.exceptions import AMQPError, ProbableAccessDeniedError
from mat.agent_utils import (AG_N2LL_ANS_BYE, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS,
                             AG_N2LL_ANS_ROUTE_ERR_ALREADY, AG_N2LL_ANS_ROUTE_OK_FULL,
                             AG_N2LL_CMD_WHO, AG_N2LL_CMD_BYE, AG_N2LL_CMD_QUERY,
                             AG_N2LL_CMD_ROUTE, AG_N2LL_CMD_UNROUTE,
                             AG_N2LL_ANS_NOT_FOR_US, AG_N2LL_ANS_ROUTE_NOK)


def _p(s):
    print(s, flush=True)


def _u():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


def _get_ngrok_bin_name() -> str:
    _s = os.uname().nodename
    _m = os.uname().machine
    if _m == 'armv7l':
        return 'ngrok_rpi'
    if _s == 'rasberrypi' or _s == 'rpi':
        return 'ngrok_rpi'
    return 'ngrok'


def check_ngrok():
    name = _get_ngrok_bin_name()
    cmd = '{} -h'.format(name)
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        _p('{} found'.format(name))
        return True


def _mq_get_ch():
    url = _u()
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


def _who(_, macs):
    return 0, ' '.join([m for m in macs if m and m != '*'])


def _bye(_, macs):
    return 0, '{} in {}'.format(AG_N2LL_ANS_BYE, macs)


def _query(_, macs):
    name = _get_ngrok_bin_name()
    _grep = 'ps aux | grep {} | grep -v grep'.format(name)
    rv = sp.run(_grep, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        return 0 , 'ngrok routed at {}'.format(macs[0])
    return 1, AG_N2LL_ANS_ROUTE_NOK.format(macs[0])


def _route_ngrok(_, macs):
    # _: ['route', '4000', <mac>]
    assert len(_) == 3

    # obtain proper ngrok name and kill any current local one
    ngrok_bin = _get_ngrok_bin_name()
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


def _unroute(_, macs):
    ngrok_bin = _get_ngrok_bin_name()
    cmd = 'killall {}'.format(ngrok_bin)
    _rv = sp.run([cmd], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    mac = macs[0]
    return 0, 'un-routed {}'.format(mac)


def _parse(s: bytes):
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

    # search the function
    cmd = s[0]
    fxn_map = {
        AG_N2LL_CMD_BYE: _bye,
        AG_N2LL_CMD_WHO: _who,
        AG_N2LL_CMD_QUERY: _query,
        AG_N2LL_CMD_ROUTE: _route_ngrok,
        AG_N2LL_CMD_UNROUTE: _unroute,
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


class ClientN2LL:
    def __init__(self, url, sig=None):
        """ ClientN2LL sends towards AgentN2LL in channel 'li_masters'
            ClientN2LL receives form AgentN2LL in channel 'li_slaves' """
        self.url = url
        self.ch_pub = None
        self.ch_sub = None
        self.tx_last = None
        self.sig = sig
        # 'dump' variable is useful to be able to test this class
        self.dump_cli_rx = None
        # N2LL client is always rx-threaded, entry point is tx()
        self.th_rx = threading.Thread(target=self._sub_n_rx)
        self.th_rx.start()

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_masters()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_slaves()

    def tx(self, _what: str):
        try:
            # client tx's to channel 'li_masters', rx from channel 'li_slaves'
            self._get_ch_pub()
            self.ch_pub.basic_publish(exchange='li_masters', routing_key='', body=_what)
            _p('<< ClientN2LL tx: {}'.format(_what))
            self.tx_last = _what
            self.ch_pub.close()
        except ProbableAccessDeniedError:
            e = 'ClientN2LL: error AMQP ProbableAccessDeniedError'
            if self.sig:
                self.sig.out.emit(self.tx_last, e)

    # careful: this collects answers from forgotten nodes :)
    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            s = body.decode()
            _p('>> ClientN2LL rx: {}'.format(s))
            self.dump_cli_rx = s
            if self.sig:
                self.sig.out.emit(self.tx_last, s)

        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', exclusive=True)
        q = rv.method.queue
        self.ch_sub.queue_bind(exchange='li_slaves', queue=q)
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()


class AgentN2LL(threading.Thread):
    def __init__(self, url):
        """ AgentN2LL receives from ClientN2LL in channel 'li_masters'
            AgentN2LL sends back to ClientN2LL in channel 'li_slaves' """
        assert(check_ngrok())
        super().__init__()
        self.url = url
        self.ch_pub = None
        self.ch_sub = None

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_slaves()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_masters()

    def run(self):
        self.loop_n2ll()

    def _do_i_quit(self, ans):
        if AG_N2LL_ANS_BYE in ans:
            # give time answer to travel back
            time.sleep(5)
            _p('quitting AG_N2LL')
            os._exit(0)

    def loop_n2ll(self):
        """ an agentN2LL spawns no more threads: receives at rx and tx back """
        _p('N2LL: listening on {}'.format(self.url.split('/')[-1]))
        while 1:
            try:
                self._sub_n_rx()
            except (Exception, AMQPError) as e:
                _p('N2LL: error rx_exc -> {}'.format(e))

    def _pub(self, _what):
        self._get_ch_pub()
        self.ch_pub.basic_publish(exchange='li_slaves', routing_key='', body=_what)
        # _p('<< N2LL: pub {}'.format(_what))
        self.ch_pub.close()

    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            # _p('>> N2LL: rx_cb {}'.format(body))
            ans = _parse(body)
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
