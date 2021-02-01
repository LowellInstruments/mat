import threading
import time

from mat.n2lx_utils import *

# todo: finish this AGENT_SMS, check my_python_snippets project
# todo: this AGENT_SMS may not follow same structure as other agents since cell communication
# todo: one SMS command must perform net_ensure_my_resolv_conf()


def _p(s):
    print(s, flush=True)


def _nok(s):
    return 1, '{} {} error'.format(AG_SMS_ERROR, s)


def _exc(s):
    return 2, '{} {} exception'.format(AG_SMS_EXCEPTION, s)


def _ok(s):
    return 0, '{} {}'.format(AG_SMS_OK, s)


class AgentN2LH_SMS(threading.Thread):
    def __init__(self, q1, q2):
        """ creates an agent for simpler SMS controller """
        super().__init__()

#     def _parse_n2lh_sms_incoming_frame(self, s):
#         """ s: '<ag_sms_cmd> <args>' """
#         cmd, *_ = s.split(' ', 1)
#         fxn_map = {
#             AG_BLE_CMD_QUERY: self.query,
#             AG_BLE_CMD_SCAN: self.scan,
#             AG_BLE_CMD_RWS: self.rws,
#             AG_BLE_END_THREAD: self.break_thread
#         }
#         fxn = fxn_map[cmd]
#
#         try:
#             # noinspection PyArgumentList
#             return fxn(s)
#         except BTLEException:
#             return _exc(s)
#
    def loop_ag_sms(self):
        """ receives SMS commands, sends back SMS answers """
        while 1:
            time.sleep(60)
            # _in =
            # _p('-> AG_SMS {}'.format(_in))
            # _out = self._parse_n2lh_sms_incoming_frame(_in)
            # _p('<- AG_SMS {}'.format(_out))
            # self.q_out.put(_out)

            # we can leave N2LH_SMS thread on demand
            # if AG_BLE_SMS_THREAD in _out[1]:
            #     _out: (0, 'AG_SMS_OK: sms_bye')
                # break

    def run(self):
        self.loop_ag_sms()
        _p('AG_SMS thread ends')

#     @staticmethod
#     def scan(s):
#         s: scan 0 5
        # _, h, t = s.split(' ')
        # sr = logger_controller_ble.ble_scan(int(h), float(t))
        # rv = ''
        # for each in sr:
        #     rv += '{} {} '.format(each.addr, each.rssi)
        # return _ok(rv.strip())

    # @staticmethod
    # def break_thread(_):
    #     return _ok(AG_BLE_END_THREAD)

    # def _cmd_ans(self, mac, c):
    #     c: STATUS_CMD
        # if not mac:
        #     return _nok('bad cmd, maybe forgot mac?')
        # rv = self.lc.command(c)
        # return _ok_or_nok(rv, c)

    # def rws(self, s):
    #     if not _mac_n_connect(s, self):
    #         return _nok(AG_BLE_CMD_RWS)
    #
    #     s: 'rws <rws_str> <mac>'
        # rws_str = s[s.index(' ') + 1: s.rindex(' ')]
        # rws_str = rws_str[:20]
        # rv = self.lc.command(RWS_CMD, rws_str)
        # if rv[0].decode() == RWS_CMD:
        #     return _ok(AG_BLE_CMD_RWS)
        # return _nok(AG_BLE_CMD_RWS)

    # def query(self, _):
    #     a = 'logger controller {}'
    #     if not self.lc:
    #         return _ok(a.format(AG_BLE_EMPTY))
    #     if not self.lc.per:
    #         return _ok(a.format(AG_BLE_EMPTY))
    #     return _ok(a.format(self.lc.per.getState()))

