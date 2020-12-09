import sys
import threading
import time
import pynng
from mat.agent_ble import AgentBLE
from pynng import Pair0
from mat.agent_utils import AG_N2LH_PATH_GPS, AG_N2LH_PATH_BLE, AG_BLE_CMD_QUERY, AG_BLE_CMD_STATUS, \
    AG_BLE_CMD_GET_TIME, AG_BLE_CMD_LS_LID, AG_BLE_CMD_BYE, AG_BLE_CMD_GET_FILE, AG_N2LH_CMD_BYE, AG_BLE_CMD_RUN, \
    AG_BLE_CMD_RWS, AG_BLE_CMD_CRC, AG_BLE_CMD_FORMAT, AG_BLE_CMD_MTS
from mat.logger_controller import RUN_CMD, RWS_CMD, STATUS_CMD
from mat.logger_controller_ble import CRC_CMD, MY_TOOL_SET_CMD, FORMAT_CMD, calc_ble_cmd_ans_timeout, FAKE_MAC_CC26X2, \
    FAKE_MAC_RN4020

PORT_N2LH = 12804


def _p(s):
    print(s, flush=True)


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
def calc_n2lh_cmd_ans_timeout(tag_n2lh):
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


class AgentN2LH(threading.Thread):
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
                _p('-> N2LH {}'.format(_in))
        except pynng.Timeout:
            _in = None
        return _in

    def _out_ans(self, a):
        # a: (int_rv, s), forward just s back
        try:
            _p('<- N2LH {}'.format(a[1]))
            self.sk.send(a[1].encode())
        except pynng.Timeout:
            # _p('_s_out timeout')
            pass

    def run(self):
        self.loop_n2lh()

    def loop_n2lh(self):
        """ create BLE and GPS threads """
        while 1:
            _check_url_syntax(self.url)
            self.sk = Pair0(send_timeout=100)
            self.sk.listen(self.url)
            self.sk.recv_timeout = 100
            th_ble = AgentBLE(threaded=1)
            th_ble.start()
            # todo: create GPS thread

            _p('ag_N2LH listening on {}'.format(self.url))
            while 1:
                # just parse format, not much content
                _in = self._in_cmd()
                _in = _good_n2lh_cmd_prefix(_in)
                if not _in:
                    # _p('bad N2LH prefix ({}) or timeout empty'.format(_in))
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
                        _p('<- N2LH {}'.format(file))
                        b = f.read()
                        # let's use a separate socket for N2LH sending out
                        sk = Pair0()
                        u_ext = 'tcp4://localhost:{}'.format(PORT_N2LH + 1)
                        sk.dial(u_ext)
                        sk.send(b)
                        sk.close()

                if _in == AG_N2LH_CMD_BYE:
                    break


class TestAgentN2LH:
    u = 'tcp4://localhost:{}'.format(PORT_N2LH)
    u_ext = 'tcp4://localhost:{}'.format(PORT_N2LH + 1)
    # m = '60:77:71:22:c8:18'
    # m = '60:77:71:22:c8:08'
    # m = FAKE_MAC_RN4020
    m = FAKE_MAC_CC26X2

    def test_constructor(self):
        ag = AgentN2LH(self.u, threaded=1)
        ag.start()
        list_of_cmd = [AG_N2LH_CMD_BYE]
        _fake_client_send_n_wait(self.u, list_of_cmd, 1000, self.m)

    def test_get_ble_file_there_send_it_here(self):
        if self.m in [FAKE_MAC_CC26X2, FAKE_MAC_RN4020]:
            assert True
            return
        ag = AgentN2LH(self.u, threaded=1)
        ag.start()
        list_of_cmd = ['get_file 2006671_low_20201004_132205.lid . 299950']
        _fake_client_send_n_wait(self.u, list_of_cmd, 1000, self.m)
        # on testing, use 2 sockets, on production, we'll see
        sk = Pair0()
        sk.listen(self.u_ext)
        sk.recv_timeout = 1000
        rv = _fake_client_rx_file(sk, '2006671_low_20201004_132205.lid', 299950)
        sk.close()
        assert rv

    def test_fw_commands(self):
        ag = AgentN2LH(self.u, threaded=1)
        ag.start()
        list_of_cmd = [AG_BLE_CMD_QUERY,
                       AG_BLE_CMD_STATUS,
                       AG_BLE_CMD_GET_TIME,
                       AG_BLE_CMD_LS_LID,
                       AG_BLE_CMD_QUERY,
                       AG_BLE_CMD_BYE]
        # recall time to BLE connect > 1 s
        _fake_client_send_n_wait(self.u, list_of_cmd, 5000, self.m)

    def test_n2lh_cmd_ans_timeout(self):
        t = calc_n2lh_cmd_ans_timeout(AG_BLE_CMD_STATUS)
        assert t == calc_ble_cmd_ans_timeout(STATUS_CMD) * 1.1


def _fake_client_rx_file(sk, filename, size):
    b = sk.recv()
    filename = '_rut_{}'.format(filename)
    with open(filename, 'wb') as f:
        f.write(b)
        f.truncate(int(size))
    sk.close()
    return len(b) == int(size)


def _fake_client_send_n_wait(_url, list_out, timeout_ms: int, mac):
    """ use for testing, on production, N2LH already uses a timeout-ed loop """
    _ = pynng.Pair0(send_timeout=timeout_ms)
    _.recv_timeout = timeout_ms
    _.dial(_url)
    now = time.perf_counter()
    for o in list_out:
        o = '{} {} {}'.format(AG_N2LH_PATH_BLE, o, mac)
        _.send(o.encode())
        _in = _.recv()
        print('\t{}'.format(_in.decode()))
    _p('done in {}'.format(time.perf_counter() - now))
    _.close()

