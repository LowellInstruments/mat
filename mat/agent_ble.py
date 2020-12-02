import threading
import time

import pytest
from mat.logger_controller_ble import LoggerControllerBLE


def _p(s):
    print(s, flush=True)


class AgentBLE(threading.Thread):
    def __init__(self, hci_if=0):
        super().__init__()
        self.lc = None
        self.h = hci_if

    def run(self):
        pass

    def connect(self, mac):
        # maybe already connected
        if self.lc:
            a = self.lc.address
            if a == mac and self.lc.per.getState() == "conn":
                return 0, 'already connected'

        # ensure we cut any last connection
        if self.lc:
            self.lc.close()

        # connecting asked mac
        _p('<- connect {} {}'.format(mac, self.h))
        self.lc = LoggerControllerBLE(mac, self.h)
        rv = self.lc.open()
        if rv:
            return 0, 'connected to {}'.format(mac)
        return 1, 'connection fail'

    def disconnect(self):
        _p('<- disconnect')
        if self.lc and self.lc.close():
            return 0, 'disconnected'
        return 0, 'not agent'

    def get_time(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.get_time()
        if len(str(rv)) == 19:
            return 0, rv
        return 1, rv

    def close(self):
        return self.disconnect()


class TestBLEAgent:
    def test_get_time(self):
        # sending commands implicitly connects
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        rv = th.get_time(mac)
        assert rv[0] == 0

    def test_get_time_thrice_few_time_same_connection(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        # the first command implicitly connects so takes > 1 second
        now = time.perf_counter()
        rv = th.get_time(mac)
        assert rv[0] == 0
        el = time.perf_counter() - now
        assert el > 1
        # the next 2 are much faster
        now = time.perf_counter()
        rv = th.get_time(mac)
        assert rv[0] == 0
        rv = th.get_time(mac)
        assert rv[0] == 0
        el = time.perf_counter() - now
        _p(el)
        assert el < .5

    def test_connect_error(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '11:22:33:44:55:66'
        rv = th.connect(mac)
        assert rv[0] == 1

    def test_connect_disconnect(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        rv = th.connect(mac)
        assert rv[0] == 0
        rv = th.disconnect()
        assert rv[0] == 0
        assert rv[1] == 'disconnected'

    def test_connect_already(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        th.connect(mac)
        rv = th.connect(mac)
        assert rv[1] == 'already connected'

    def test_disconnect_not_agent(self):
        th = AgentBLE()
        rv = th.disconnect()
        assert rv[1] == 'not agent'


