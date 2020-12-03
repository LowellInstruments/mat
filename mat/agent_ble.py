import threading
import time
from mat.logger_controller import STOP_CMD, STATUS_CMD
from mat.logger_controller_ble import LoggerControllerBLE
import queue


def _p(s):
    print(s, flush=True)


def _mac(s):
    return s.rsplit(' ', 1)[-1]


class AgentBLE(threading.Thread):
    def __init__(self, hci_if=0):
        super().__init__()
        self.lc = None
        self.h = hci_if
        self.q_in = queue.Queue()
        self.q_out = queue.Queue()

    def _parse(self, s):
        # s: '<cmd> <args> <mac>'
        cmd, _ = s.split(' ', 1)
        fxn_map = {
            'status': self.status,
            'connect': self.connect,
            'disconnect': self.disconnect,
            'get_time': self.get_time,
            'set_time': self.set_time,
            'ls_lid': self.ls_lid,
            'ls_not_lid': self.ls_not_lid,
            'stop': self.stop,
            # 'get_file': self.get_file
        }
        fxn = fxn_map[cmd]
        # noinspection PyArgumentList
        return fxn(s)

    def run(self):
        while 1:
            _in = self.q_in.get()
            # needed because of testing threads
            if _in == 'bye':
                break
            _out = self._parse(_in)
            self.q_out.put(_out)

    def status(self, s):
        # s: 'status <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(STATUS_CMD)
        if rv[0] == b'STS' and len(rv[1]) == 4:
            return 0, rv
        return 1, rv

    def connect(self, s):
        # s: 'connect <mac>' but it may be already
        mac = _mac(s)
        if self.lc:
            a = self.lc.address
            if a == mac and self.lc.per.getState() == "conn":
                return 0, 'already connected'

        # cut any current connection w/ different mac
        if self.lc:
            self.lc.close()

        # connecting asked mac
        _p('<- connect {} {}'.format(mac, self.h))
        self.lc = LoggerControllerBLE(mac, self.h)
        rv = self.lc.open()
        if rv:
            return 0, 'connected to {}'.format(mac)
        return 1, 'connection fail'

    def disconnect(self, _=None):
        # does not use any parameter
        _p('<- disconnect')
        if self.lc and self.lc.close():
            return 0, 'disconnected'
        return 0, 'was not connected'

    def get_time(self, s):
        # s: 'get_time <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.get_time()
        if len(str(rv)) == 19:
            return 0, str(rv)
        return 1, rv

    def set_time(self, s):
        # s: 'set_time <mac>'
        mac = _mac(s)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.sync_time()
        print(rv)
        if rv == [b'STM', b'00']:
            return 0, rv
        return 1, rv

    def ls_lid(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.ls_lid()
        if type(rv) == dict:
            return 0, rv
        return 1, rv

    def ls_not_lid(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.ls_not_lid()
        if type(rv) == dict:
            return 0, rv
        return 1, rv

    def stop(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(STOP_CMD)
        if rv == [b'STP', b'00']:
            return 0, 'logger stopped'
        return 1, 'logger not stopped'

    # def get_file(self, mac, file, fol, size):
    #     rv = self.connect(mac)
    #     if rv[0] == 1:
    #         return rv
    #     todo: pass sig as parameter
        # rv = self.lc.get_file(file, fol, size)
        # if rv:
        #     return 0, 'file {} size {}'.format(file, size)
        # return 1, 'err get_file {} size {}'.format(file, 0)
    #
    def close(self):
        return self.disconnect()


class TestBLEAgent:
    m = '60:77:71:22:c8:08'

    def test_disconnect_was_not_connected(self):
        ag = AgentBLE()
        ag.start()
        # skip connect on purpose
        mac = self.m
        s = '{} {}'.format('disconnect', mac)
        rv = _q(ag, s)
        assert rv[1] == 'was not connected'
        _q(ag, 'bye')

    def test_connect_disconnect(self):
        ag = AgentBLE()
        ag.start()
        mac = self.m
        s = '{} {}'.format('disconnect', mac)
        _q(ag, s)
        s = '{} {}'.format('connect', mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        s = '{} {}'.format('disconnect', mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        assert rv[1] == 'disconnected'
        _q(ag, 'bye')

    def test_connect_error(self):
        # may take a bit more time, 3 retries connect
        ag = AgentBLE()
        ag.start()
        mac = '11:22:33:44:55:66'
        s = '{} {}'.format('disconnect', mac)
        _q(ag, s)
        s = '{} {}'.format('connect', mac)
        rv = _q(ag, s)
        assert rv[0] == 1
        _q(ag, 'bye')

    def test_connect_already(self):
        mac = self.m
        ag = AgentBLE()
        ag.start()
        s = '{} {}'.format('disconnect', mac)
        _q(ag, s)
        s = '{} {}'.format('connect', mac)
        _q(ag, s)
        s = '{} {}'.format('connect', mac)
        rv = _q(ag, s)
        assert rv[1] == 'already connected'
        _q(ag, 'bye')

    def test_get_time_thrice_few_time_same_connection(self):
        ag = AgentBLE()
        ag.start()
        mac = self.m
        s = '{} {}'.format('disconnect', mac)
        _q(ag, s)
        # the first command implicitly connects so takes > 1 second
        now = time.perf_counter()
        s = '{} {}'.format('get_time', mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        assert el > 1
        _p('1st GTM {} took {}'.format(rv[1], el))
        # the next 2 are much faster
        now = time.perf_counter()
        s = '{} {}'.format('get_time', mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        s = '{} {}'.format('get_time', mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        _p('2nd & 3rd GTM {} took {}'.format(rv[1], el))
        assert el < .5
        _q(ag, 'bye')

    def test_set_time(self):
        mac = self.m
        ag = AgentBLE()
        ag.start()
        s = '{} {}'.format('disconnect', mac)
        _q(ag, s)
        s = '{} {}'.format('set_time', mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        _q(ag, 'bye')

    # def test_get_file(self):
    #     # this may not output text during a long time
    #     th = AgentBLE()
    #     th.start()
    #     th.disconnect()
    #     mac = '60:77:71:22:C8:18'
    #     file = '2006671_low_20201004_132205.lid'
    #     size = 299950
    #     rv = th.get_file(mac, file, '.', size)
    #     assert rv[0] == 0

    def test_ls_lid(self):
        mac = self.m
        ag = AgentBLE()
        ag.start()
        s = 'disconnect {}'.format(mac)
        _q(ag, s)
        s = 'ls_lid {}'.format(mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0
        _q(ag, 'bye')

    def test_ls_not_lid(self):
        mac = self.m
        ag = AgentBLE()
        ag.start()
        s = 'disconnect {}'.format(mac)
        _q(ag, s)
        s = 'ls_not_lid {}'.format(mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0
        _q(ag, 'bye')

    def test_stop(self):
        mac = self.m
        ag = AgentBLE()
        ag.start()
        s = 'stop {}'.format(mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        _q(ag, 'bye')


def _q(_ag, _in):
    _ag.q_in.put(_in)
    # needed because of testing threads
    if _in == 'bye':
        return
    _out = _ag.q_out.get()
    return _out
