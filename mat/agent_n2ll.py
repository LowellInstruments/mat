import random
import threading
import time
import subprocess as sp
import pika
import os
from getmac import get_mac_address
from pika.exceptions import AMQPError, ProbableAccessDeniedError
from mat.agent_n2lh import PORT_N2LH
from mat.agent_utils import AG_N2LL_ANS_BYE, AG_N2LL_ANS_QUERY, AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS, \
    AG_N2LL_ANS_ROUTE_ERR_ALREADY, AG_N2LL_ANS_ROUTE_OK, AG_N2LL_CMD_ROUTE_NX, AG_N2LL_CMD_WHO, AG_N2LL_CMD_ROUTE_N2LH, \
    AG_N2LL_CMD_QUERY, AG_N2LL_CMD_BYE, AG_N2LL_CMD_ROUTE_KILL

PORT_NX_SERVER = 4000
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
    _grep = 'ps aux | grep nxserver | grep -v grep'
    _rv = sp.run(_grep, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    cond_nx = _rv.returncode == 0
    # todo: set proper executable ___name___ here below
    _grep = 'ps aux | grep _____name___agent___ | grep -v grep'
    _rv = sp.run(_grep, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    cond_ag = _rv.returncode == 0
    s = AG_N2LL_ANS_QUERY
    s = s.format(cond_nx, cond_ag, macs)
    return 0, s


def _route_ngrok(macs, port):

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


def _route_nx(_, macs):
    return _route_ngrok(macs, PORT_NX_SERVER)


def _route_agent(_, macs):
    return _route_ngrok(macs, PORT_N2LH)


def _kill(_, macs):
    ngrok_bin = _get_ngrok_bin_name()
    cmd = 'killall {}'.format(ngrok_bin)
    _rv = sp.run([cmd], shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return 0, '{} done at {}'.format(cmd, macs)


def _parse(s: bytes):
    # s: AG_N2LL_CMD_QUERY <mac>
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
        mac = s[1]
        if mac not in _my_macs:
            return b'error lnp: cmd not for us'

    # search the function
    cmd = s[0]
    fxn_map = {
        AG_N2LL_CMD_BYE: _bye,
        AG_N2LL_CMD_WHO: _who,
        AG_N2LL_CMD_QUERY: _query,
        AG_N2LL_CMD_ROUTE_NX: _route_nx,
        AG_N2LL_CMD_ROUTE_N2LH: _route_agent,
        AG_N2LL_CMD_ROUTE_KILL: _kill
    }
    fxn = fxn_map[cmd]

    # noinspection PyArgumentList
    return fxn(s, _my_macs)


class AgentN2LL(threading.Thread):
    def __init__(self, url, threaded):
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
        """ agentN2LL has no threads: rx and tx back """
        _p('ag_N2LL listening on {}'.format(self.url.split('/')[-1]))
        while 1:
            try:
                self._sub_n_rx()
            except (Exception, AMQPError) as e:
                _p('agent_N2LL rx_exc -> {}'.format(e))

    def _pub(self, _what):
        self._get_ch_pub()
        self.ch_pub.basic_publish(exchange='li_slaves', routing_key='', body=_what)
        # _p('<- slave  pub: {}'.format(_what))
        self.ch_pub.close()

    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            # _p('-> slave  rx_cb: {}'.format(body))
            ans = _parse(body)
            # ans: (0, description)
            self._pub(ans[1])

        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', durable=True, exclusive=True)
        q = rv.method.queue
        self.ch_sub.queue_bind(exchange='li_masters', queue=q)
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()


class ClientN2LL:
    def __init__(self, url, sig=None):
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