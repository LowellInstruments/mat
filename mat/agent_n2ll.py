import random
import threading
import time
import subprocess as sp
import pika
import os
from getmac import get_mac_address
from pika.exceptions import AMQPError, ProbableAccessDeniedError
from mat.agent_utils import AG_N2LL_ANS_BYE, AG_N2LL_ANS_QUERY, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS, \
    AG_N2LL_ANS_ROUTE_ERR_ALREADY, AG_N2LL_ANS_ROUTE_OK, AG_N2LL_CMD_WHO, AG_N2LL_CMD_BYE, AG_N2LL_CMD_QUERY, \
    AG_N2LL_CMD_ROUTE, AG_N2LL_CMD_UNROUTE


TIME_COLLISIONS_S = 3


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
    cmd = '{} -h'.format(_get_ngrok_bin_name())
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        return True


def _mq_get_ch():
    url = _u()
    _pars = pika.URLParameters(url)
    _pars.socket_timeout = 5
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
        return 0 , 'ngrok running at {}'.format(macs[0])
    return 1, 'ngrok NOT running at {}'.format(macs[0])


def _route_ngrok(_, macs):
    return 0, 'hello'

    # random to avoid collisions
    _tc = random.random() * TIME_COLLISIONS_S
    _p('sleeping {:.2f} s...'.format(_tc))
    time.sleep(_tc)

    # short_name for log file
    log_file = '/tmp/ngrok.log'

    # obtain proper ngrok name and kill any current local one
    ngrok_bin = _get_ngrok_bin_name()
    cmd = 'killall {}'.format(ngrok_bin)
    sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    # remove any previous ngrok log file
    cmd = 'rm {}'.format(log_file)
    _rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if b'permission denied' in _rv.stderr:
        return 1, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS

    # Popen() daemons ngrok, although cannot check return code
    cmd = '{} tcp {} -log={}'.format(ngrok_bin, port, log_file)
    _p(cmd)
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
    pad = ' ' * 23
    s = AG_N2LL_ANS_ROUTE_OK
    s = s.format(macs[0], pad, port, pad, u)
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
        return b'error lnp: cmd empty'

    # parse n2ll stuff
    s = s.decode().split(' ')

    # who am I
    _my_macs = [get_mac_address(interface='wlo1'),
                get_mac_address(interface='wlan0'),
                '*']

    # is this frame for us
    if len(s) >= 2:
        # todo: do this for more universal mac names
        mac = s[-1]
        if mac not in _my_macs:
            return 1, 'cmd not for us'

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

    # noinspection PyArgumentList
    return fxn(s, _my_macs)


class AgentN2LL(threading.Thread):
    def __init__(self, url, threaded):
        """ receives from channel 'li_masters', sends back in 'li_slaves' """
        super().__init__()
        self.url = url
        self.ch_pub = None
        self.ch_sub = None
        if not threaded:
            self.loop_n2ll()

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_slaves()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_masters()

    def run(self):
        self.loop_n2ll()

    def loop_n2ll(self):
        """ agentN2LL spawns no more threads: rx and tx back """
        _p('ag_N2LL: listening on {}'.format(self.url.split('/')[-1]))
        while 1:
            try:
                self._sub_n_rx()
            except (Exception, AMQPError) as e:
                _p('agent_N2LL rx_exc -> {}'.format(e))

    def _pub(self, _what):
        self._get_ch_pub()
        self.ch_pub.basic_publish(exchange='li_slaves', routing_key='', body=_what)
        # _p('<- ag_N2LL: pub {}'.format(_what))
        self.ch_pub.close()

    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            # _p('-> ag_N2LL: rx_cb {}'.format(body))
            ans = _parse(body)
            # ans: (0, description) send to channel 'li_slaves'
            self._pub(ans[1])

        # receive from channel 'li_masters'
        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', durable=True, exclusive=True)
        q = rv.method.queue
        self.ch_sub.queue_bind(exchange='li_masters', queue=q)
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()


class ClientN2LL:
    def __init__(self, url, sig=None):
        """ sends to channel 'li_masters', receives back in 'li_slaves' """
        self.url = url
        self.ch_pub = None
        self.ch_sub = None
        self.tx_last = None
        self.sig = sig
        # an N2LL client loop is always threaded, entry point is tx()
        self.th_rx = threading.Thread(target=self.loop_n2ll)
        self.th_rx.start()

    def loop_n2ll(self):
        self._sub_n_rx()

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_masters()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_slaves()

    def tx(self, _what: str):
        try:
            # client tx's to channel 'li_masters', rx from channel 'li_slaves'
            self._get_ch_pub()
            self.ch_pub.basic_publish(exchange='li_masters', routing_key='', body=_what)
            _p('<- ClientN2LL master pub: {}'.format(_what))
            self.tx_last = _what
            self.ch_pub.close()
        except ProbableAccessDeniedError:
            e = 'error AMQP ProbableAccessDeniedError'
            self.sig.emit(self.tx_last, e)

    # careful: this may collect answers from forgotten nodes :)
    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            s = body.decode()
            _p('-> ClientN2LL master rx: {}'.format(s))
            self.sig.out.emit(self.tx_last, s)

        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', exclusive=True)
        q = rv.method.queue
        self.ch_sub.queue_bind(exchange='li_slaves', queue=q)
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()