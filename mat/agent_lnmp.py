import threading
import pika
from getmac import get_mac_address
from pika.exceptions import AMQPError, ProbableAccessDeniedError


def _p(s):
    print(s, flush=True)


def _u():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


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


# def _cmd_query(cmd, macs) -> str:
#     _grep = 'ps aux | grep {} | grep -v grep'.format(cmd)
#     _rv = sp.run(_grep, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
#     cond = _rv.returncode == 0
#     s = '{} {} at {}'.format(SYM_TICK, cmd, macs[0])
#     e = '{} no {} at {}'.format(SYM_CROSS, cmd, macs[0])
#     return s if cond else e
#
#
# def _cmd_nle_query(macs) -> str:
#     return _cmd_query('main_nle_s.py', macs)
#
#
# def _cmd_nx_query(macs) -> str:
#     return _cmd_query('nxserver', macs)
#
#
# def _cmd_ngrok_query(macs) -> str:
#     return _cmd_query(get_ngrok_bin_name(), macs)


class AgentLLP(threading.Thread):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.ch_pub = None
        self.ch_sub = None
        # todo: do this for more universal mac names
        self._my_macs = [get_mac_address(interface='wlo1'),
                         get_mac_address(interface='wlan0'),
                         '*']

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_slaves()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_masters()

    def _who(self) -> str:
        return ' '.join([_ for _ in self._my_macs if _ and _ != '*'])

    def _parse(self, s: bytes):
        if not s:
            return b'error lnp: cmd empty'

        # parse lnp stuff
        cmd, mac, *_ = s.split(' ', 2)

        # is this frame for us
        if mac not in self._my_macs:
            return b'error lnp: cmd not for us'

        # search the function
        fxn_map = {
            'bye!': self.bye,
            'who': self._who
            #     elif cmd == 'gr_nx':
            #         _ = cmd_ngrok_to_nx(_my_macs, mac_wildcard)
            #     elif cmd == 'gr_nle':
            #         _ = cmd_ngrok_to_nle(_my_macs, mac_wildcard)
            #     elif cmd == 'gr_stop':
            #         _ = cmd_ngrok_kill(_my_macs)
            #     elif cmd == 'gr_query':
            #         _ = _cmd_ngrok_query(_my_macs)

        }
        fxn = fxn_map[cmd]
        # noinspection PyArgumentList
        return fxn(s)

    def run(self):
        while 1:
            try:
                self._sub_n_rx()
                print('agent loop end')
            except (Exception, AMQPError) as e:
                print('agent_lnmp rx_exc -> {}'.format(e))

    def _pub(self, _what):
        self._get_ch_pub()
        self.ch_pub.basic_publish(exchange='li_slaves', routing_key='', body=_what)
        print('<- tx slave:  {}'.format(_what))
        self.ch_pub.close()

    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            print('-> rx slave:  {}'.format(body))
            ans = self._parse(body)
            self._pub(ans)

        print('q')
        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', durable=True, exclusive=True)
        q = rv.method.queue
        print('c')
        self.ch_sub.queue_bind(exchange='li_masters', queue=q)
        print('d')
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()

    @staticmethod
    def bye(_):
        return 0, 'bye you from ble'

    def query(self, _):
        a = 'agent ble is {}'
        if not self.lc:
            return 0, a.format('empty')
        if not self.lc.per:
            return 0, a.format('empty')
        return 0, a.format(self.lc.per.getState())


class ClientLLP:
    # pubs to 'li_masters', subs from 'li_slaves'
    def __init__(self, url, sig=None):
        self.url = url
        self.ch_pub = None
        self.ch_sub = None
        self.th_sub = threading.Thread(target=self._sub_n_rx)
        self.th_sub.start()
        self.tx_last = None
        self.sig = sig

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_masters()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_slaves()

    def tx(self, _what: str):
        try:
            self._get_ch_pub()
            self.ch_pub.basic_publish(exchange='li_masters', routing_key='', body=_what)
            _p('<- pub master: {}'.format(_what))
            self.tx_last = _what
            self.ch_pub.close()
        except ProbableAccessDeniedError:
            e = 'error AMQP'
            self.sig.emit(self.tx_last, e)

    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            _p(body.decode())

        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', exclusive=True)
        q = rv.method.queue
        print('a')
        self.ch_sub.queue_bind(exchange='li_slaves', queue=q)
        print('b')
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()


class MyTestLLPAgent:
    _url = _u()

    def my_test_llp_cmd(self):
        ag = AgentLLP(self._url)
        ag.start()
        list_of_cmd = ['who']
        ac = ClientLLP(self._url)
        for cmd in list_of_cmd:
            ac.tx(cmd)


if __name__ == '__main__':
    _t = MyTestLLPAgent()
    _t.my_test_llp_cmd()
