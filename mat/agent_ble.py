import threading
import time
from mat import logger_controller_ble
from mat.agent_utils import AG_BLE_ERR, AG_BLE_CMD_STATUS, AG_BLE_CMD_CONNECT, AG_BLE_CMD_DISCONNECT, \
    AG_BLE_CMD_GET_TIME, AG_BLE_CMD_SET_TIME, AG_BLE_CMD_LS_LID, AG_BLE_CMD_LS_NOT_LID, AG_BLE_CMD_STOP, \
    AG_BLE_CMD_GET_FILE, AG_BLE_CMD_BYE, AG_BLE_CMD_QUERY, AG_BLE_CMD_SCAN, AG_BLE_CMD_SCAN_LI, AG_BLE_ANS_CONN_ALREADY, \
    AG_BLE_ANS_CONN_OK, AG_BLE_ANS_CONN_ERR, AG_BLE_ANS_DISC_OK, AG_BLE_ANS_DISC_ALREADY, AG_BLE_ANS_STOP_OK, \
    AG_BLE_ANS_BYE, AG_BLE_ANS_STOP_ERR, AG_BLE_EMPTY, AG_BLE_CMD_GET_FW_VER
from mat.logger_controller import STOP_CMD, STATUS_CMD, SET_TIME_CMD, FIRMWARE_VERSION_CMD
from mat.logger_controller_ble import LoggerControllerBLE, is_a_li_logger
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
    return rv


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
        return 1, _e('{} {}'.format(AG_BLE_CMD_GET_TIME, rv[1].decode()))

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

    def set_time(self, s):
        # s: 'set_time <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.sync_time()
        print(rv)
        if rv == [b'STM', b'00']:
            return 0, '{} 00'.format(SET_TIME_CMD)
        return 1, _e('{} {}'.format(AG_BLE_CMD_SET_TIME, rv[1].decode()))

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
    # m = '60:77:71:22:c8:08'
    m = '60:77:71:22:c8:18'

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


def _q(_ag, _in):
    _ag.q_in.put(_in)
    # needed because of testing threads
    if _in == AG_BLE_CMD_BYE:
        return
    _out = _ag.q_out.get()
    return _out
