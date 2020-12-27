import threading
import time
import parse
import pynng
from mat.agent_n2lh_ble import AgentN2LH_BLE
from pynng import Pair0
from mat.agent_utils import AG_N2LH_PATH_GPS, AG_N2LH_PATH_BLE, AG_BLE_CMD_QUERY, AG_BLE_CMD_STATUS, \
    AG_BLE_CMD_GET_TIME, AG_BLE_CMD_LS_LID, AG_BLE_CMD_GET_FILE, AG_N2LH_CMD_BYE, AG_BLE_CMD_RUN, \
    AG_BLE_CMD_RWS, AG_BLE_CMD_CRC, AG_BLE_CMD_FORMAT, AG_BLE_CMD_MTS
from mat.logger_controller import RUN_CMD, RWS_CMD, STATUS_CMD
from mat.logger_controller_ble import CRC_CMD, MY_TOOL_SET_CMD, FORMAT_CMD, calc_ble_cmd_ans_timeout, FAKE_MAC_CC26X2, \
    FAKE_MAC_RN4020

PORT_N2LH = 12804


def _p(s):
    print(s, flush=True)


class ClientN2LH():
    """ ClientN2LH transmits command to AgentN2LH via pynng
        ClientN2LH receives answer from AgentN2LH via pynng """
    def __init__(self, s, url):
        super().__init__()
        self.cmd = s
        self.url = url

    def tx(self):
        # s: 'connect <MAC>' ~ 30s
        _c = self.cmd.split(' ')[0]
        _till = calc_n2lh_cmd_ans_timeout_secs(_c) * 1000
        sk = pynng.Pair0(send_timeout=1000)
        sk.recv_timeout = _till
        sk.dial(self.url)
        _o = '{} {}'.format(AG_N2LH_PATH_BLE, self.cmd)
        sk.send(_o.encode())
        _in = sk.recv().decode()
        sk.close()
        return _in


class AgentN2LH(threading.Thread):
    """ AgentN2LH receives command from ClientN2LH via pynng
        AgentN2LH enqueues command towards AgentBLE
        AgentN2LH dequeues the answer from AgentBLE
        AgentN2LH sends answers towards ClientN2LH via pynng """
    def __init__(self, n2lh_url, threaded):
        super().__init__()
        self.sk = None
        self.url = n2lh_url
        # an AgentN2LH has 1 BLE thread, 1 GPS thread...
        if not threaded:
            self.loop_n2lh()

    def _in_cmd(self):
        """ receive NLE client commands, silent timeouts """
        try:
            _in = self.sk.recv()
            if _in:
                _in = _in.decode()
                _p('>> N2LH {}'.format(_in))
        except pynng.Timeout:
            _in = None
        return _in

    def _out_ans(self, a):
        # a: (int_rv, s), forward just s back
        try:
            _p('<< N2LH {}'.format(a[1]))
            self.sk.send(a[1].encode())
        except pynng.Timeout:
            # _p('_s_out timeout')
            pass

    def run(self):
        self.loop_n2lh()

    def loop_n2lh(self):
        """ rx commands via pynng and enqueue them for BLE and GPS threads"""
        while 1:
            _check_url_syntax(self.url)
            self.sk = Pair0(send_timeout=100)
            self.sk.listen(self.url)
            self.sk.recv_timeout = 100
            th_ble = AgentN2LH_BLE(threaded=1)
            th_ble.start()
            # todo: create GPS thread

            _p('N2LH: listening on {}'.format(self.url))
            while 1:
                # just parse format, not content
                _in = self._in_cmd()
                _in = _good_n2lh_cmd_prefix(_in)

                # timeout or bad N2LH prefix
                if not _in:
                    # _p('n2lh_in nope')
                    continue

                # good N2LH command for our threads
                th_ble.q_in.put(_in)
                _out = th_ble.q_out.get()
                self._out_ans(_out)

                # more to do, forward file in case of get_file
                if _in.startswith(AG_BLE_CMD_GET_FILE) and _out[0] == 0:
                    # _in: 'get_file <name> <fol> <size> <mac>'
                    file = _in.split(' ')[1]
                    with open(file, 'rb') as f:
                        _p('<< N2LH {}'.format(file))
                        b = f.read()

                        # use a separate socket port + 1 to tx file
                        # todo: nope, fix this since ngrok can only expose 1 port
                        sk = Pair0()
                        _ = parse.parse('{}://{}:{:d}', self.url)
                        u_ext = '{}://{}:{}'.format(_[0], _[1], _[2] + 1)
                        _p(u_ext)
                        sk.dial(u_ext)
                        sk.send(b)
                        sk.close()

                if _in.startswith(AG_N2LH_CMD_BYE):
                    # this can 'return' or 'break'
                    return


def _good_n2lh_cmd_prefix(s):
    if not s or len(s) < 4:
        return ''
    if s == AG_N2LH_CMD_BYE:
        return s

    # 'ble <cmd>...' -> <cmd> ...'
    if s[:3] in (AG_N2LH_PATH_BLE, AG_N2LH_PATH_GPS):
        return s[4:]


def _check_url_syntax(s):
    _transport = s.split(':')[0]
    _adr = s.split('//')[0]
    if _adr.startswith('localhost') or _adr.startswith('127.0'):
        _p('careful, localhost not same as IP')
    assert _transport in ['tcp4', 'tcp6']
    assert _transport not in ['tcp']


# used by N2LH clients such as GUIs
def calc_n2lh_cmd_ans_timeout_secs(tag_n2lh):
    _tag_map = {
        AG_BLE_CMD_RUN: RUN_CMD,
        AG_BLE_CMD_RWS: RWS_CMD,
        AG_BLE_CMD_CRC: CRC_CMD,
        # NOR memories have Write, Erase slow
        AG_BLE_CMD_FORMAT: FORMAT_CMD,
        AG_BLE_CMD_MTS: MY_TOOL_SET_CMD
    }

    # default value is status, simplest
    tag_mat = _tag_map.setdefault(tag_n2lh, STATUS_CMD)

    # some more time than BLE MAT library commands
    return calc_ble_cmd_ans_timeout(tag_mat) * 1.1


# for testing purposes
url_lh = 'tcp4://localhost:{}'.format(PORT_N2LH)
url_lh_ext = 'tcp4://localhost:{}'.format(PORT_N2LH + 1)
if __name__ == '__main__':
    ag = AgentN2LH(url_lh, threaded=1)
    ag.start()
    # give agent time to start
    time.sleep(1)
    list_of_cmd = [AG_BLE_CMD_QUERY,
                   AG_BLE_CMD_STATUS,
                   AG_BLE_CMD_GET_TIME,
                   AG_BLE_CMD_LS_LID,
                   AG_BLE_CMD_QUERY]
                   # AG_BLE_CMD_BYE]

    for c in list_of_cmd:
        cmd = '{} {}'.format(c, FAKE_MAC_CC26X2)
        ClientN2LH(cmd, url_lh, None)
        time.sleep(.1)

