import socket
import threading
from pika.exceptions import ProbableAccessDeniedError
from mat.n2ll_utils import (
    mq_exchange_for_masters,
    mq_exchange_for_slaves)


class ClientN2LL:
    def __init__(self, url, sig=None):

        """ ClientN2LL pubs to channel 'li_masters', subs to 'li_slaves'
            AgentN2LL (all N of them) pub to 'li_slaves', sub to 'li_masters' """

        self.url = url
        self.ch_pub = None
        self.ch_sub = None
        self.tx_last = None
        self.sig = sig
        # 'dump' variable is useful to be able to test this class
        self.dump_cli_rx = None

        # N2LL client rx ALWAYS threaded, entry point is tx()
        self.th_rx = threading.Thread(target=self.n2ll_client_sub_n_rx)
        self.th_rx.start()

    def _get_ch_pub(self):
        self.ch_pub = mq_exchange_for_masters()

    def _get_ch_sub(self):
        self.ch_sub = mq_exchange_for_slaves()

    def n2ll_client_pub(self, _what: str):
        try:
            # client TX to channel 'li_masters', RX from 'li_slaves'
            self._get_ch_pub()
            self.ch_pub.basic_publish(exchange='li_masters', routing_key='', body=_what)
            print('<- ClientN2LL tx: {}'.format(_what))
            self.tx_last = _what
            self.ch_pub.close()

        except ProbableAccessDeniedError:
            e = 'ClientN2LL: error -> AMQP ProbableAccessDeniedError'
            if self.sig:
                self.sig.out.emit(self.tx_last, e)

    def n2ll_client_sub_n_rx(self):
        try:
            self._sub_n_rx()
        except socket.gaierror as e:
            print('ClientN2LL: exc -> {}'.format(e))

    # note: this collects answers from ALL slaves :)
    def _sub_n_rx(self):
        def _rx_cb(ch, method, properties, body):
            s = body.decode()
            print('-> ClientN2LL rx: {}'.format(s))
            self.dump_cli_rx = s

            # update GUI back, if any
            if self.sig:
                self.sig.out.emit(self.tx_last, s)

        self._get_ch_sub()
        rv = self.ch_sub.queue_declare(queue='', exclusive=True)
        q = rv.method.queue
        self.ch_sub.queue_bind(exchange='li_slaves', queue=q)
        self.ch_sub.basic_consume(queue=q, on_message_callback=_rx_cb, auto_ack=True)
        self.ch_sub.start_consuming()
