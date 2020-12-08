import json
import threading
import time
from mat import logger_controller_ble
from mat.agent_utils import *
from mat.logger_controller import STOP_CMD, STATUS_CMD, FIRMWARE_VERSION_CMD, LOGGER_INFO_CMD, \
    CALIBRATION_CMD, SENSOR_READINGS_CMD, DO_SENSOR_READINGS_CMD, RESET_CMD, SD_FREE_SPACE_CMD, REQ_FILE_NAME_CMD, \
    DEL_FILE_CMD, RUN_CMD, RWS_CMD, SWS_CMD, LOGGER_HSA_CMD_W, LOGGER_INFO_CMD_W
from mat.logger_controller_ble import LoggerControllerBLE, is_a_li_logger, FORMAT_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, \
    MOBILE_CMD, LOG_EN_CMD, UP_TIME_CMD, MY_TOOL_SET_CMD, CONFIG_CMD
import queue


def _p(s):
    print(s, flush=True)


def _stringify_dir_ans(_d_a):
    if _d_a == b'ERR':
        return AG_BLE_ERR
    # _d_a: {'file.lid': 2182}
    rv = ''
    for k, v in _d_a.items():
        rv += '{} {} '.format(k, v)
    if rv == '':
        rv = AG_BLE_ANS_DIR_EMPTY
    return rv.rstrip()


def _mac_n_connect(s, ag_ble):
    mac = s.rsplit(' ', 1)[-1]
    rv = ag_ble.connect(mac)
    if rv[0] == 0:
        return mac
    return None


def _sp(s, i):
    return s.rsplit(' ')[i]


def _ok_or_nok(rv, c):
    if rv[0] == c.encode():
        p = '' if len(rv) == 1 else rv[1].decode()
        return 0, '{} OK: {}'.format(c, p)
    return 1, '{} ERR'


def _e(s):
    print(s)


# can be threaded
class AgentBLE(threading.Thread):
    def __init__(self, threaded, hci_if=0):
        super().__init__()
        self.lc = None
        self.h = hci_if
        # an AgentBLE has no threads
        self.q_in = queue.Queue()
        self.q_out = queue.Queue()
        if not threaded:
            self.loop_ble()

    def _parse(self, s):
        # s: '<cmd> <args> <mac>'
        cmd, *_ = s.split(' ', 1)
        fxn_map = {
            AG_BLE_CMD_STATUS: self.status,
            AG_BLE_CMD_CONNECT: self.connect,
            AG_BLE_CMD_DISCONNECT: self.disconnect,
            AG_BLE_CMD_GET_TIME: self.get_time,
            AG_BLE_CMD_SET_TIME: self.set_time,
            AG_BLE_CMD_LS_LID: self.ls_lid,
            AG_BLE_CMD_LS_NOT_LID: self.ls_not_lid,
            AG_BLE_CMD_STOP: self.stop,
            AG_BLE_CMD_BYE: self.bye,
            AG_BLE_CMD_QUERY: self.query,
            AG_BLE_CMD_SCAN: self.scan,
            AG_BLE_CMD_SCAN_LI: self.scan_li,
            AG_BLE_CMD_GET_FW_VER: self.get_fw_ver,
            AG_BLE_CMD_RLI: self.rli,
            AG_BLE_CMD_RHS: self.rhs,
            AG_BLE_CMD_FORMAT: self.format,
            AG_BLE_CMD_EBR: self.ebr,
            AG_BLE_CMD_MBL: self.mbl,
            AG_BLE_CMD_LOG_TOGGLE: self.log_en,
            AG_BLE_CMD_GSR: self.gsr,
            AG_BLE_CMD_GSR_DO: self.gsr_do,
            AG_BLE_CMD_RESET: self.reset,
            AG_BLE_CMD_UPTIME: self.uptime,
            AG_BLE_CMD_CFS: self.cfs,
            AG_BLE_CMD_RFN: self.rfn,
            AG_BLE_CMD_MTS: self.mts,
            AG_BLE_CMD_CONFIG: self.config,
            AG_BLE_CMD_DEL_FILE: self.del_file,
            AG_BLE_CMD_RUN: self.cmd_run,
            AG_BLE_CMD_RWS: self.rws,
            AG_BLE_CMD_SWS: self.sws,
            AG_BLE_CMD_WLI: self.wli,
            AG_BLE_CMD_WHS: self.whs,
            AG_BLE_CMD_GET_FILE: self.get_file,
            AG_BLE_CMD_DWG_FILE: self.dwg_file
        }
        fxn = fxn_map[cmd]

        # noinspection PyArgumentList
        return fxn(s)

    def loop_ble(self):
        while 1:
            _in = self.q_in.get()
            _out = self._parse(_in)
            self.q_out.put(_out)
            if _in == AG_BLE_CMD_BYE:
                break

    def run(self):
        self.loop_ble()

    @staticmethod
    def scan(s):
        # s: scan 0 5
        _, h, t = s.split(' ')
        sr = logger_controller_ble.ble_scan(int(0), float(t))
        rv = ''
        for each in sr:
            rv += '{} {} '.format(each.addr, each.rssi)
        return 0, rv.strip()

    @staticmethod
    def scan_li(s):
        # s: scan_li 0 5
        _, h, t = s.split(' ')
        sr = logger_controller_ble.ble_scan(int(0), float(t))
        rv = ''
        for each in sr:
            if is_a_li_logger(each.rawData):
                rv += '{} {} '.format(each.addr, each.rssi)
        return 0, rv.strip()

    def connect(self, s):
        # s: 'connect <mac>' but it may be already
        mac = s.rsplit(' ', 1)[-1]
        if self.lc:
            a = self.lc.address
            if a == mac and self.lc.per.getState() == "conn":
                return 0, AG_BLE_ANS_CONN_ALREADY

        # cut any current connection w/ different mac
        if self.lc:
            self.lc.close()

        # connecting asked mac
        _p('<- {} {} {}'.format(AG_BLE_CMD_CONNECT, mac, self.h))
        self.lc = LoggerControllerBLE(mac, self.h)
        if self.lc.open():
            return 0, '{} to {}'.format(AG_BLE_ANS_CONN_OK, mac)
        return 1, AG_BLE_ANS_CONN_ERR

    def disconnect(self, _=None):
        # does not use any parameter
        _p('<- {}'.format(AG_BLE_CMD_DISCONNECT))
        if self.lc and self.lc.close():
            return 0, AG_BLE_ANS_DISC_OK
        return 0, AG_BLE_ANS_DISC_ALREADY

    def get_time(self, s):
        if not _mac_n_connect(s, self):
            return 1, 'get_time error'

        rv = self.lc.get_time()
        # in case of get_time(), rv is already a string
        if len(str(rv)) == 19:
            return 0, str(rv)
        return 1, 'get_time error'

    def config(self, s):
        if not _mac_n_connect(s, self):
            return 1, 'config error'

        # '$' symbol as useful guard since <cfg> has spaces
        cfg = s.split('$')[1]
        rv = self.lc.send_cfg(json.loads(cfg))
        if rv[0].decode() == CONFIG_CMD:
            return 0, 'CFG OK'
        return 1, 'config error'

    def rli(self, s):
        if not _mac_n_connect(s, self):
            return 1, 'RLI error'

        # read all RLI fields
        a = ''
        for _ in ('SN', 'CA', 'BA', 'MA'):
            rv = self.lc.command(LOGGER_INFO_CMD, _)
            a += '{} {} '.format(_, rv[1].decode())
        if 'ERR' in a:
            return 1, 'RLI error'
        return 0, a.rstrip()

    def rhs(self, s):
        if not _mac_n_connect(s, self):
            return 1, 'RHS error'

        # read all RHS fields
        a = ''
        for _ in ('TMO', 'TMR', 'TMA', 'TMB', 'TMC'):
            rv = self.lc.command(CALIBRATION_CMD, _)
            a += '{} {} '.format(_, rv[1].decode())
        if 'ERR' in a:
            return 1, 'RHS error'
        return 0, a.rstrip()

    def _cmd_ans(self, mac, c):
        # c: STATUS_CMD
        if not mac:
            return 1, 'connection ERR'
        rv = self.lc.command(c)
        return _ok_or_nok(rv, c)

    def status(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), STATUS_CMD)

    def get_fw_ver(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), FIRMWARE_VERSION_CMD)

    def format(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), FORMAT_CMD)

    def ebr(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), ERROR_WHEN_BOOT_OR_RUN_CMD)

    def mbl(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), MOBILE_CMD)

    def log_en(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), LOG_EN_CMD)

    def gsr(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), SENSOR_READINGS_CMD)

    def gsr_do(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), DO_SENSOR_READINGS_CMD)

    def reset(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), RESET_CMD)

    def uptime(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), UP_TIME_CMD)

    def cfs(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), SD_FREE_SPACE_CMD)

    def rfn(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), REQ_FILE_NAME_CMD)

    def mts(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), MY_TOOL_SET_CMD)

    def set_time(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), AG_BLE_CMD_SET_TIME)

    def del_file(self, s):
        # s: 'del_file <filename> <mac>'
        if not _mac_n_connect(s, self):
            return 1, 'del_file error'

        # delete the file
        name = s.split(' ')[1]
        rv = self.lc.command(DEL_FILE_CMD, name)
        if rv[0].decode() == DEL_FILE_CMD:
            return 0, AG_BLE_CMD_DEL_FILE
        return 1, _e(AG_BLE_CMD_DEL_FILE)

    def ls_lid(self, s):
        if not _mac_n_connect(s, self):
            return 1, 'ls_lid error'
        rv = self.lc.ls_lid()
        if type(rv) == dict:
            return 0, _stringify_dir_ans(rv)
        return 1, rv

    def ls_not_lid(self, s):
        if not _mac_n_connect(s, self):
            return 1, 'ls_not_lid error'
        rv = self.lc.ls_not_lid()
        if type(rv) == dict:
            return 0, _stringify_dir_ans(rv)
        return 1, rv

    def stop(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), STOP_CMD)

    # prevent same name as thread function run()
    def cmd_run(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), RUN_CMD)

    def rws(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), RWS_CMD)

    def sws(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), SWS_CMD)

    def whs(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), LOGGER_HSA_CMD_W)

    def wli(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), LOGGER_INFO_CMD_W)

    @staticmethod
    def bye(_):
        return 0, AG_BLE_ANS_BYE

    def query(self, _):
        a = 'agent_ble logger controller ble is {}'
        if not self.lc:
            return 0, a.format(AG_BLE_EMPTY)
        if not self.lc.per:
            return 0, a.format(AG_BLE_EMPTY)
        return 0, a.format(self.lc.per.getState())

    def get_file(self, s):
        # s: 'get_file <file> <fol> <size> <mac>
        file, fol, size = _sp(s, 1), _sp(s, 2), _sp(s, 3)

        if not _mac_n_connect(s, self):
            return 1, 'get_file error'

        if self.lc.get_file(file, fol, size):
            return 0, 'get_file OK: {} {}'.format(file, size)
        return 1, 'get_file error: {} {}'.format(file, size)

    def dwg_file(self, s):
        # s: 'dwg_file <file> <fol> <size> <mac>
        file, fol, size = _sp(s, 1), _sp(s, 2), _sp(s, 3)

        if not _mac_n_connect(s, self):
            return 1, 'dwg_file error'

        if self.lc.dwg_file(file, fol, size):
            return 0, 'dwg_file OK: {} {}'.format(file, size)
        return 1, 'get_file error: {} {}'.format(file, size)

    def close(self):
        return self.disconnect()


class TestBLEAgent:
    m = '60:77:71:22:c8:08'
    # m = '60:77:71:22:c8:18'

    def test_disconnect_was_not_connected(self):
        ag = AgentBLE(threaded=1)
        ag.start()
        # skip connect() on purpose
        mac = self.m
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        rv = _q(ag, s)
        assert rv[1] == AG_BLE_ANS_DISC_ALREADY
        _q(ag, AG_BLE_CMD_BYE)

    def test_connect_disconnect(self):
        ag = AgentBLE(threaded=1)
        ag.start()
        mac = self.m
        # todo: can we remove this disconnects in the tests?
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        assert rv[1] == AG_BLE_ANS_DISC_OK
        _q(ag, AG_BLE_CMD_BYE)

    def test_connect_error(self):
        # may take a bit more time, 3 retries connect
        ag = AgentBLE(threaded=1)
        ag.start()
        bad_mac = '11:22:33:44:55:66'
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, bad_mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, bad_mac)
        rv = _q(ag, s)
        assert rv[0] == 1
        _q(ag, AG_BLE_CMD_BYE)

    def test_connect_already(self):
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        rv = _q(ag, s)
        assert rv[1] == AG_BLE_ANS_CONN_ALREADY
        _q(ag, AG_BLE_CMD_BYE)

    def test_get_time_thrice_few_time_same_connection(self):
        ag = AgentBLE(threaded=1)
        ag.start()
        mac = self.m
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        # the first command implicitly connects so takes > 1 second
        now = time.perf_counter()
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        assert el > 1
        _p('1st {} took {}'.format(AG_BLE_CMD_GET_TIME, el))
        # the next 2 are much faster
        now = time.perf_counter()
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        _p('2nd & 3rd {} took {}'.format(AG_BLE_CMD_GET_TIME, el))
        assert el < .5
        _q(ag, AG_BLE_CMD_BYE)

    def test_set_time(self):
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_SET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)

    def test_get_file(self):
        # this long test may take a couple minutes
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        file = '2006671_low_20201004_132205.lid'
        size = 299950
        fol = '.'
        s = '{} {} {} {} {}'
        s = s.format(AG_BLE_CMD_GET_FILE, file, fol, size, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)

    def test_ls_lid(self):
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_LS_LID, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)

    def test_ls_not_lid(self):
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_LS_NOT_LID, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)

    def test_stop(self):
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_STOP, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)

    def test_scan(self):
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} 0 5'.format(AG_BLE_CMD_SCAN)
        rv = _q(ag, s)
        assert rv[0] == 0
        _p(rv[1])
        _q(ag, AG_BLE_CMD_BYE)

    def test_scan_li(self):
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} 0 5'.format(AG_BLE_CMD_SCAN_LI)
        rv = _q(ag, s)
        assert rv[0] == 0
        _p(rv[1])
        _q(ag, AG_BLE_CMD_BYE)

    def test_config_cmd(self):
        _cfg = {
            "DFN": "low",
            "TMP": 0, "PRS": 0,
            "DOS": 1, "DOP": 1, "DOT": 1,
            "TRI": 10, "ORI": 10, "DRI": 900,
            "PRR": 8,
            "PRN": 4,
            "STM": "2012-11-12 12:14:00",
            "ETM": "2030-11-12 12:14:20",
            "LED": 1
        }
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_STOP, mac)
        _q(ag, s)
        # _cfg: dict -> string
        _cfg = json.dumps(_cfg)
        s = '{} ${}$ {}'.format(AG_BLE_CMD_CONFIG, _cfg, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)

    def test_mts_cmd(self):
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_MTS, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)

    def test_any_cmd(self):
        mac = self.m
        ag = AgentBLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_LS_LID, mac)
        rv = _q(ag, s)
        _p(rv)
        s = '{} {}'.format(AG_BLE_CMD_LS_NOT_LID, mac)
        rv = _q(ag, s)
        _p(rv)

        assert rv[0] == 0
        _q(ag, AG_BLE_CMD_BYE)


def _q(_ag, _in):
    _ag.q_in.put(_in)
    # needed because of testing threads
    if _in == AG_BLE_CMD_BYE:
        return
    _out = _ag.q_out.get()
    return _out
