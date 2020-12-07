import json
import threading
import time
from mat import logger_controller_ble
from mat.agent_utils import AG_BLE_ERR, AG_BLE_CMD_STATUS, AG_BLE_CMD_CONNECT, AG_BLE_CMD_DISCONNECT, \
    AG_BLE_CMD_GET_TIME, AG_BLE_CMD_SET_TIME, AG_BLE_CMD_LS_LID, AG_BLE_CMD_LS_NOT_LID, AG_BLE_CMD_STOP, \
    AG_BLE_CMD_GET_FILE, AG_BLE_CMD_BYE, AG_BLE_CMD_QUERY, AG_BLE_CMD_SCAN, AG_BLE_CMD_SCAN_LI, AG_BLE_ANS_CONN_ALREADY, \
    AG_BLE_ANS_CONN_OK, AG_BLE_ANS_CONN_ERR, AG_BLE_ANS_DISC_OK, AG_BLE_ANS_DISC_ALREADY, AG_BLE_ANS_STOP_OK, \
    AG_BLE_ANS_BYE, AG_BLE_ANS_STOP_ERR, AG_BLE_EMPTY, AG_BLE_CMD_GET_FW_VER, AG_BLE_CMD_RLI, AG_BLE_CMD_RHS, \
    AG_BLE_CMD_FORMAT, AG_BLE_CMD_EBR, AG_BLE_CMD_MBL, AG_BLE_CMD_LOG_TOGGLE, AG_BLE_CMD_GSR, AG_BLE_CMD_GSR_DO, \
    AG_BLE_CMD_RESET, AG_BLE_CMD_UPTIME, AG_BLE_CMD_CFS, AG_BLE_CMD_RFN, AG_BLE_CMD_MTS, AG_BLE_CMD_CONFIG, \
    AG_BLE_ANS_DIR_EMPTY, AG_BLE_CMD_DEL_FILE
from mat.logger_controller import STOP_CMD, STATUS_CMD, SET_TIME_CMD, FIRMWARE_VERSION_CMD, LOGGER_INFO_CMD, \
    CALIBRATION_CMD, SENSOR_READINGS_CMD, DO_SENSOR_READINGS_CMD, RESET_CMD, SD_FREE_SPACE_CMD, REQ_FILE_NAME_CMD, \
    DEL_FILE_CMD
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


def _mac(s):
    return s.rsplit(' ', 1)[-1]


def _sp(s, i):
    return s.rsplit(' ')[i]


def _e(s):
    return 'error {}'.format(s)


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
            AG_BLE_CMD_GET_FILE: self.get_file,
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

    def status(self, s):
        # s: 'status <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(STATUS_CMD)
        a = '{} {}'.format(STATUS_CMD, rv[1].decode())
        if rv[0] == b'STS' and len(rv[1]) == 4:
            return 0, a
        return 1, _e(a)

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
        mac = _mac(s)
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
        rv = self.lc.open()
        if rv:
            return 0, '{} to {}'.format(AG_BLE_ANS_CONN_OK, mac)
        return 1, AG_BLE_ANS_CONN_ERR

    def disconnect(self, _=None):
        # does not use any parameter
        _p('<- {}'.format(AG_BLE_CMD_DISCONNECT))
        if self.lc and self.lc.close():
            return 0, AG_BLE_ANS_DISC_OK
        return 0, AG_BLE_ANS_DISC_ALREADY

    def get_time(self, s):
        # s: 'get_time <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.get_time()
        # in case of get_time(), this already is a string
        if len(str(rv)) == 19:
            return 0, str(rv)
        return 1, _e('{}'.format(AG_BLE_CMD_GET_TIME))

    def rli(self, s):
        # s: 'rli <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv

        # read all RLI fields
        who = ('SN', 'CA', 'BA', 'MA')
        a = ''
        for _ in who:
            rv = self.lc.command(LOGGER_INFO_CMD, _)
            a += '{} {} '.format(_, rv[1].decode())
        if 'ERR' in a:
            return 1, _e(a)
        return 0, a.rstrip()

    def rhs(self, s):
        # s: 'rhs<mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv

        # read all RHS fields
        who = ('TMO', 'TMR', 'TMA', 'TMB', 'TMC')
        a = ''
        for _ in who:
            rv = self.lc.command(CALIBRATION_CMD, _)
            a += '{} {} '.format(_, rv[1].decode())
        if 'ERR' in a:
            return 1, _e(a)
        return 0, a.rstrip()

    def get_fw_ver(self, s):
        # s: 'get_fw_ver <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(FIRMWARE_VERSION_CMD)
        a = '{} {}'.format(FIRMWARE_VERSION_CMD, rv[1].decode())
        if rv[0] == b'GFV' and len(rv[1]) == 8:
            return 0, a
        return 1, _e(a)

    def format(self, s):
        # s: 'format <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(FORMAT_CMD)
        cond = rv[0].decode() == FORMAT_CMD
        if cond:
            return 0, 'format ok'
        return 1, _e(AG_BLE_CMD_FORMAT)

    def ebr(self, s):
        # s: 'ebr <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(ERROR_WHEN_BOOT_OR_RUN_CMD)
        cond = rv[0].decode() == ERROR_WHEN_BOOT_OR_RUN_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_EBR)

    def mbl(self, s):
        # s: 'mbl <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(MOBILE_CMD)
        cond = rv[0].decode() == MOBILE_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_MBL)

    def log_en(self, s):
        # s: 'log <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(LOG_EN_CMD)
        cond = rv[0].decode() == LOG_EN_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_LOG_TOGGLE)

    def gsr(self, s):
        # s: 'gsr <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(SENSOR_READINGS_CMD)
        cond = rv[0].decode() == SENSOR_READINGS_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_GSR)

    def gsr_do(self, s):
        # s: 'gsr_do <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(DO_SENSOR_READINGS_CMD)
        cond = rv[0].decode() == DO_SENSOR_READINGS_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_GSR_DO)

    def reset(self, s):
        # s: 'reset <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(RESET_CMD)
        cond = rv[0].decode() == RESET_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_RESET)

    def uptime(self, s):
        # s: 'uptime <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(UP_TIME_CMD)
        cond = rv[0].decode() == UP_TIME_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_UPTIME)

    def cfs(self, s):
        # todo: check this number, is too big, 100 MB?
        # s: 'cfs <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(SD_FREE_SPACE_CMD)
        cond = rv[0].decode() == SD_FREE_SPACE_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_CFS)

    def rfn(self, s):
        # s: 'rfn <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(REQ_FILE_NAME_CMD)
        cond = rv[0].decode() == REQ_FILE_NAME_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_RFN)

    def mts(self, s):
        # s: 'mts <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(MY_TOOL_SET_CMD)
        cond = rv[0].decode() == MY_TOOL_SET_CMD
        if cond:
            return 0, rv[1].decode()
        return 1, _e(AG_BLE_CMD_MTS)

    def set_time(self, s):
        # s: 'set_time <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.sync_time()
        if rv == [b'STM', b'00']:
            return 0, '{} 00'.format(AG_BLE_CMD_SET_TIME)
        return 1, _e('{}'.format(AG_BLE_CMD_SET_TIME))

    def config(self, s):
        # s: 'config <cfg> <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        # '$' symbol as useful guard since <cfg> has spaces
        cfg = s.split('$')[1]
        rv = self.lc.send_cfg(json.loads(cfg))
        cond = rv[0].decode() == CONFIG_CMD
        if cond:
            return 0, AG_BLE_CMD_CONFIG
        return 1, _e(AG_BLE_CMD_CONFIG)

    def del_file(self, s):
        # s: 'del_file <filename> <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv

        # delete the file
        name = s.split(' ')[1]
        rv = self.lc.command(DEL_FILE_CMD, name)
        cond = rv[0].decode() == DEL_FILE_CMD
        if cond:
            return 0, AG_BLE_CMD_DEL_FILE
        return 1, _e(AG_BLE_CMD_DEL_FILE)


    def ls_lid(self, s):
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.ls_lid()
        if type(rv) == dict:
            return 0, _stringify_dir_ans(rv)
        return 1, rv

    def ls_not_lid(self, s):
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.ls_not_lid()
        if type(rv) == dict:
            return 0, _stringify_dir_ans(rv)
        return 1, rv

    def stop(self, s):
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(STOP_CMD)
        if rv == [b'STP', b'00']:
            return 0, AG_BLE_ANS_STOP_OK
        return 1, AG_BLE_ANS_STOP_ERR

    @staticmethod
    def bye(_):
        return 0, AG_BLE_ANS_BYE

    def query(self, _):
        a = 'agent ble is {}'
        if not self.lc:
            return 0, a.format(AG_BLE_EMPTY)
        if not self.lc.per:
            return 0, a.format(AG_BLE_EMPTY)
        return 0, a.format(self.lc.per.getState())

    def get_file(self, s):
        # s: 'get_file <file> <fol> <size> <mac>
        mac = _mac(s)
        file = _sp(s, 1)
        fol = _sp(s, 2)
        size = _sp(s, 3)

        rv = self.connect(mac)
        if rv[0] == 1:
            return rv

        # todo: do this and pass sig as parameter
        rv = self.lc.get_file(file, fol, size)
        if rv:
            return 0, 'file {} size {}'.format(file, size)
        return 1, _e('{} {} size {}'.format(AG_BLE_CMD_GET_FILE, file, 0))

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
