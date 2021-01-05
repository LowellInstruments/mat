import queue
import threading
import time
import parse
import pynng
from pynng import Pair0
from mat.agent_n2lh_ble import AgentN2LH_BLE
from mat.agent_utils import (AG_N2LH_PATH_GPS, AG_N2LH_PATH_BLE, AG_BLE_CMD_QUERY, AG_BLE_CMD_STATUS,
                             AG_BLE_CMD_GET_TIME, AG_BLE_CMD_LS_LID, AG_BLE_CMD_GET_FILE, AG_BLE_CMD_RUN,
                             AG_BLE_CMD_RWS, AG_BLE_CMD_CRC, AG_BLE_CMD_FORMAT, AG_BLE_CMD_MTS, AG_N2LH_END_THREAD,
                             AG_N2LH_PATH_BASE, AG_BLE_END_THREAD, AG_BLE_ANS_GET_FILE_OK, AG_BLE_OK,
                             AG_BLE_ANS_GET_FILE_ERR, AG_BLE_CMD_DWG_FILE)
from mat.logger_controller import RUN_CMD, RWS_CMD, STATUS_CMD
from mat.logger_controller_ble import CRC_CMD, MY_TOOL_SET_CMD, FORMAT_CMD, \
    calc_ble_cmd_ans_timeout, DWG_FILE_CMD, GET_FILE_CMD
from mat.logger_controller_ble_dummy import FAKE_MAC_CC26X2


PORT_N2LH = 12804
N2LH_DEFAULT_URL = 'tcp4://localhost:{}'.format(PORT_N2LH)
N2LH_CLI_SEND_TIMEOUT_MS = 5000


def _p(s):
    print(s, flush=True)


class ClientN2LH():
    """ ClientN2LH    <-- pynng --> AgentN2LH  <-- queues --> AgentN2LH_BLE
        'ble cmd mac' ------------> ble cmd mac ------------> cmd mac """
    def __init__(self, s, url, fol):
        super().__init__()
        self.cmd = s
        self.url = url
        self.fol = fol

    def do(self, n2lh_path, rx_timeout_ms):
        """ builds and sends N2LH command """
        # path: AG_N2LH_PATH_BASE, AG_N2LH_PATH_BLE...
        _c = self.cmd.split(' ')[0]
        sk = pynng.Pair0(send_timeout=N2LH_CLI_SEND_TIMEOUT_MS)
        sk.recv_timeout = int(rx_timeout_ms)
        sk.dial(self.url)

        # sends N2LH command via pynng, wait for answer w/ timeout
        _o = '{} {}'.format(n2lh_path, self.cmd)
        # _o: ble connect <mac>
        sk.send(_o.encode())
        _in = sk.recv().decode()

        # extra steps in case of requesting files
        if _c in (AG_BLE_CMD_GET_FILE, AG_BLE_CMD_DWG_FILE):
            # did AgentN2LH_BLE GET / DWG successfully
            _in = sk.recv().decode()
            if AG_BLE_ANS_GET_FILE_OK in _in:
                # once GET / DWG worked, receive file from AgentN2LH_BLE
                b = sk.recv()
                filename = self.cmd.split(' ')[1]
                size = self.cmd.split(' ')[3]
                filepath = '{}/{}'.format(self.fol, filename)
                with open(filepath, 'wb') as f:
                    f.write(b)
                    f.truncate(int(size))

        sk.close()
        return _in


class AgentN2LH(threading.Thread):
    """ ClientN2LH    <-- pynng --> AgentN2LH  <-- queues --> AgentN2LH_BLE
        'ble cmd mac' ------------> ble cmd mac ------------> cmd mac """
    def __init__(self, n2lh_url):
        super().__init__()
        self.sk = None
        self.url = n2lh_url

    def _in_cmd(self):
        try:
            _in = self.sk.recv()
            if _in:
                _in = _in.decode()
                _p('>> N2LH {}'.format(_in))
        except pynng.Timeout:
            _in = None
        return _in

    def _out_ans(self, a):
        # a: (int_rv, s), forward just 's' back
        try:
            _p('<< N2LH {}'.format(a[1]))
            self.sk.send(a[1].encode())
        except pynng.Timeout:
            # _p('_s_out timeout')
            pass

    def run(self):
        self.loop_n2lh()

    def loop_n2lh(self):
        """ creates one BLE thread, one GPS thread... """
        _check_url_syntax(self.url)
        self.sk = Pair0(send_timeout=100)
        self.sk.listen(self.url)
        self.sk.recv_timeout = 100
        self.q_to_ble = queue.Queue()
        self.q_from_ble = queue.Queue()
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()

        _p('N2LH: listening on {}'.format(self.url))
        while 1:
            # _in: <n2lh_path> <command>
            _in = self._in_cmd()
            _in = _good_n2lh_cmd_prefix(_in)

            # pynng timeout or bad N2LH prefix
            if not _in:
                # _p('n2lh_in nope')
                continue

            # leave N2LH thread on demand
            if _in.startswith(AG_N2LH_END_THREAD):
                ans = (0, 'AG_N2LH_OK: end_thread')
                self._out_ans(ans)
                return 0

            # pass FORWARD incoming N2LH frame to sub-agents like BLE
            self.q_to_ble.put(_in)
            _out = self.q_from_ble.get()
            self._out_ans(_out)

            # additionally, pass BACK file to ClientN2LH in case of GET / DWG
            if _in.startswith(AG_BLE_CMD_GET_FILE) or \
                _in.startswith(AG_BLE_CMD_DWG_FILE):
                if _out[0] != 0:
                    self._out_ans((0, AG_BLE_ANS_GET_FILE_ERR))
                    continue
                self._out_ans((0, AG_BLE_ANS_GET_FILE_OK))

                # _in: 'get_ / dwg_file <name> <fol> <size> <mac>'
                file = _in.split(' ')[1]
                fol = _in.split(' ')[2]
                path = '{}/{}'.format(fol, file)
                with open(path, 'rb') as f:
                    # extra send file backwards
                    _p('<< N2LH {}'.format(path))
                    b = f.read()
                    self.sk.dial(self.url)
                    self.sk.send(b)


def _good_n2lh_cmd_prefix(s):
    """ checks N2LH format and path are OK """
    if not s or len(s) < 4:
        return ''

    # good paths
    n2lh_paths = [
        AG_N2LH_PATH_BASE,
        AG_N2LH_PATH_BLE,
        AG_N2LH_PATH_GPS
    ]

    # s: 'ble <cmd>...' -> <cmd> ...'
    if s[:3] in n2lh_paths:
        return s[4:]


def _check_url_syntax(s):
    _transport = s.split(':')[0]
    _adr = s.split('//')[0]
    if _adr.startswith('localhost') or _adr.startswith('127.0'):
        _p('careful, localhost not same as IP')
    assert _transport in ['tcp4', 'tcp6']
    assert _transport not in ['tcp']


def calc_n2lh_cmd_ans_timeout_ms(s):
    # s: dwg_file dummy_1129.txt . 16384 <mac>
    tag_n2lh = s.split(' ')[0]

    _tag_map = {
        AG_BLE_CMD_RUN: RUN_CMD,
        AG_BLE_CMD_RWS: RWS_CMD,
        AG_BLE_CMD_CRC: CRC_CMD,
        # NOR memories have Write, Erase slow
        AG_BLE_CMD_FORMAT: FORMAT_CMD,
        AG_BLE_CMD_MTS: MY_TOOL_SET_CMD
    }

    # default value is STATUS_CMD, simplest
    tag_mat_lib = _tag_map.setdefault(tag_n2lh, STATUS_CMD)

    # override when variable-time commands
    if tag_n2lh in (AG_BLE_CMD_DWG_FILE, AG_BLE_CMD_GET_FILE):
        size = s.split(' ')[3]
        delay_start_dwg_get_s = 5
        timeout_rx_file = int((int(size) / 3000) + delay_start_dwg_get_s)
        timeout_rx_file_ms = timeout_rx_file * 1000
        print('**** {}'.format(timeout_rx_file_ms))
        return timeout_rx_file_ms

    # slight more time than BLE MAT library commands, in milliseconds
    return calc_ble_cmd_ans_timeout(tag_mat_lib) * 1.1 * 1000


# for N2LH testing purposes
if __name__ == '__main__':
    url_lh = 'tcp4://localhost:{}'.format(PORT_N2LH)
    mac = FAKE_MAC_CC26X2
    ag = AgentN2LH(url_lh)
    th_ag_ble = threading.Thread(target=ag.loop_n2lh)
    th_ag_ble.start()

    # give time agent to start
    time.sleep(1)

    # send client commands
    list_of_cmd = [AG_BLE_CMD_QUERY,
                   AG_BLE_CMD_STATUS,
                   AG_BLE_CMD_GET_TIME,
                   AG_BLE_CMD_LS_LID,
                   AG_BLE_CMD_QUERY]

    for c in list_of_cmd:
        t = calc_n2lh_cmd_ans_timeout_ms(c)
        cmd = '{} {}'.format(c, mac)
        ClientN2LH(cmd, url_lh).do(AG_N2LH_PATH_BLE, t)

    # make N2LH_BLE and N2LH_BASE threads end
    cmd = '{} {}'.format(AG_BLE_END_THREAD, mac)
    ClientN2LH(cmd, url_lh).do(AG_N2LH_PATH_BLE, 1000)
    cmd = '{} {}'.format(AG_N2LH_END_THREAD, mac)
    ClientN2LH(cmd, url_lh).do(AG_N2LH_PATH_BASE, 1000)