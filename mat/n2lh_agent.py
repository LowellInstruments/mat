import queue
import socket
import threading
import pynng
from pynng import Pair0
from mat.logger_controller import RUN_CMD, RWS_CMD, STATUS_CMD
from mat.logger_controller_ble import CRC_CMD, MY_TOOL_SET_CMD, FORMAT_CMD, calc_ble_cmd_ans_timeout, \
    BLE_CONNECTION_TIMEOUT, BLE_CONNECTION_RETRIES, BLE_DISCONNECTION_TIME
from mat.n2lh_agent_ble import AgentN2LH_BLE
from mat.n2lx_utils import (AG_N2LH_PATH_GPS, AG_N2LH_PATH_BLE, AG_BLE_CMD_GET_FILE, AG_BLE_CMD_RUN,
                            AG_BLE_CMD_RWS, AG_BLE_CMD_CRC, AG_BLE_CMD_FORMAT, AG_BLE_CMD_MTS, AG_N2LH_END_THREAD,
                            AG_N2LH_PATH_BASE, AG_BLE_ANS_GET_FILE_OK,
                            AG_BLE_ANS_GET_FILE_ERR, AG_BLE_CMD_DWG_FILE, AG_BLE_CMD_CONNECT, AG_BLE_CMD_SCAN,
                            AG_BLE_CMD_SCAN_LI, AG_BLE_CMD_DISCONNECT, AG_N2LH_NOTIFICATION)


PORT_N2LH = 12804
N2LH_DEFAULT_URL = 'tcp4://localhost:{}'.format(PORT_N2LH)


class AgentN2LH(threading.Thread):
    """ ClientN2LH  <-- pynng -->   AgentN2LH    <-- queues -->  AgentN2LH_BLE
        ------------------------>  'ble cmd mac' ------------->  'cmd mac' """

    def __init__(self, n2lh_url):
        super().__init__()
        self.sk = None
        self.url = n2lh_url

    def _in_cmd_from_cli(self):
        try:
            _in = self.sk.recv()
            if _in:
                _in = _in.decode()
                _p('-> N2LH {}'.format(_in))
        except pynng.Timeout:
            _in = None
        return _in

    def _out_ans_to_cli(self, a):
        # a: (int_rv, s), forward just the 's' part back
        try:
            _p('<- N2LH {}'.format(a[1]))
            self.sk.send(a[1].encode())
        except pynng.Timeout:
            # _p('_s_out timeout')
            pass

    def _out_notification_to_cli(self, s: str):
        try:
            _p('<- N2LH_notification {}'.format(s))
            self.sk.send(s.encode())
        except pynng.Timeout:
            # _p('_s_out_notification timeout')
            pass

    def loop_n2lh_agent(self):
        try:
            self._loop_n2lh_agent()
        except Exception as e:
            _p('N2LH: agent exc -> {}'.format(e))

    def _loop_n2lh_agent(self):
        """ creates one BLE thread, one GPS thread... """
        _check_url_syntax(self.url)
        self.sk = Pair0(send_timeout=100)
        self.sk.listen(self.url)
        self.sk.recv_timeout = 100
        # can set queues' timeout in q.get() calls, like for notifications
        self.q_to_ble = queue.Queue()
        self.q_from_ble = queue.Queue()
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()

        _p('N2LH: listening on {}'.format(self.url))
        while 1:
            # todo: test BLE disconnection notification
            try:
                # timeout-ed queue to allow exceptions from BLE
                _ntf = self.q_from_ble.get(block=False, timeout=.1)
                # _ntf: (1, 'ntf some_text')
                _ntf = _check_n2lh_notifications(_ntf[1])
                if _ntf:
                    self._out_notification_to_cli(_ntf)
            except queue.Empty:
                pass

            # -> _in: <n2lh_path> <command>
            _in = self._in_cmd_from_cli()
            _in = _check_n2lh_cmd_path(_in)
            if not _in:
                # pynng timeout or bad N2LH prefix
                continue

            # -> quit! leave N2LH thread on demand
            if _in.startswith(AG_N2LH_END_THREAD):
                ans = (0, 'AG_N2LH_OK: end_thread')
                self._out_ans_to_cli(ans)
                return 0

            # -> _in towards sub-agents like BLE
            self.q_to_ble.put(_in)

            # <- grab the answer!
            _out = self.q_from_ble.get()
            self._out_ans_to_cli(_out)

            # in case of DWG command, pass BACK file to ClientN2LH
            if _in.startswith(AG_BLE_CMD_DWG_FILE):

                # first, DWG return value
                if _out[0] != 0:
                    self._out_ans_to_cli((0, AG_BLE_ANS_GET_FILE_ERR))
                    continue
                self._out_ans_to_cli((0, AG_BLE_ANS_GET_FILE_OK))

                # _in: 'dwg_file <name> <fol> <size> <mac>'
                file = _in.split(' ')[1]
                path = '/tmp/{}'.format(file)
                with open(path, 'rb') as f:
                    # <- send file backwards
                    _p('<- N2LH back-warding {}'.format(path))
                    b = f.read()
                    self.sk.dial(self.url)
                    self.sk.send(b)


def _check_n2lh_cmd_path(s):
    """ checks N2LH command format and path are OK """

    if not s or len(s) < 4:
        return ''

    # good paths, ex: AG_N2LH_PATH_BLE is 'ble'
    n2lh_paths = [
        AG_N2LH_PATH_BASE,
        AG_N2LH_PATH_BLE,
        AG_N2LH_PATH_GPS
    ]

    # s: 'ble <cmd>...' -> <cmd> ...'
    if s[:3] in n2lh_paths:
        return s[4:]


def _check_n2lh_notifications(s):
    """ checks N2LH notification format is OK """

    if not s or len(s) < 4:
        return ''

    # good paths, ex: AG_N2LH_NOTIFICATION is 'ntf'
    n2lh_notifications = [
        AG_N2LH_NOTIFICATION
    ]

    # s: 'ntf <something>'
    if s[:3] in n2lh_notifications:
        return s[4:]


def _check_url_syntax(s):
    _transport = s.split(':')[0]
    _adr = s.split('//')[0]
    if _adr.startswith('localhost') or _adr.startswith('127.0'):
        _p('careful, localhost not same as IP')
    assert _transport in ['tcp4', 'tcp6']
    assert _transport not in ['tcp']


def calc_n2lh_cmd_ans_timeout_ms(s):
    """
    calculate how long to wait for N2LH answer
    a bit longer, than for BLE commands :)
    """

    # s: 'dwg_file dummy_1129.txt . 16384 <mac>'
    tag_n2lh = s.split(' ')[0]

    # N2LH commands > slight more than MAT lib commands
    _tag_map = {
        AG_BLE_CMD_RUN: RUN_CMD,
        AG_BLE_CMD_RWS: RWS_CMD,
        AG_BLE_CMD_CRC: CRC_CMD,
        # NOR memories have Write, Erase slow
        AG_BLE_CMD_FORMAT: FORMAT_CMD,
        AG_BLE_CMD_MTS: MY_TOOL_SET_CMD
    }
    tag_mat_lib = _tag_map.setdefault(tag_n2lh, STATUS_CMD)
    till = calc_ble_cmd_ans_timeout(tag_mat_lib) * 1.1

    # override 'till' for variable-time commands like get and download
    if tag_n2lh in (AG_BLE_CMD_DWG_FILE, AG_BLE_CMD_GET_FILE):
        size = s.split(' ')[2]
        delay_start_dwg_get_s = 10
        till = int((int(size) / 2000) + delay_start_dwg_get_s)

    # override 'till' for special commands like scan and connect
    if tag_n2lh == AG_BLE_CMD_CONNECT:
        till = (BLE_CONNECTION_TIMEOUT * BLE_CONNECTION_RETRIES) + 1
    elif tag_n2lh in (AG_BLE_CMD_SCAN_LI, AG_BLE_CMD_SCAN):
        till = int(float(s.split(' ')[-1]) + 1)
    elif tag_n2lh == AG_BLE_CMD_DISCONNECT:
        till = BLE_DISCONNECTION_TIME

    # debug purposes
    # s = 'N2LH: timeout \'{}\' will be {}'
    # _p(PC.OKBLUE + s.format(tag_n2lh, t_s) + PC.ENDC)

    # returned as milliseconds
    return till * 1000


def _p(s):
    print(s, flush=True)
