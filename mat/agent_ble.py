import threading
import time

from mat.logger_controller import STOP_CMD, SET_TIME_CMD, STATUS_CMD
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

    def set_time(self, mac):
        # ------------ this crashes because we need argument time :)
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(SET_TIME_CMD)
        print(rv)
        if rv == [b'STM', b'00']:
            return 0, rv
        return 1, rv

    def status(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(STATUS_CMD)
        if rv[0] == b'STS' and len(rv[1]) == 4:
            return 0, rv
        return 1, rv

    def ls_lid(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        # todo: return my 0 and 1 here and below not_lid()
        return self.lc.ls_lid()

    def ls_not_lid(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        return self.lc.ls_not_lid()

    def stop_logger(self, mac):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        rv = self.lc.command(STOP_CMD)
        if rv == [b'STP', b'00']:
            return 0, 'logger stopped'
        return 1, 'logger not stopped'

    def get_file(self, mac, file, fol, size):
        rv = self.connect(mac)
        if rv[0] == 1:
            return rv
        # todo: pass sig as parameter
        rv = self.lc.get_file(file, fol, size)
        if rv:
            return 0, 'file {} size {}'.format(file, size)
        return 1, 'err get_file {} size {}'.format(file, 0)

    def close(self):
        return self.disconnect()


class TestBLEAgent:
    def test_status(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        rv = th.status(mac)
        assert rv[0] == 0

    def test_set_time(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        rv = th.set_time(mac)
        assert rv[0] == 0

    def test_get_file(self):
        # this may not output text during a long time
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        file = '2006671_low_20201004_132205.lid'
        size = 299950
        rv = th.get_file(mac, file, '.', size)
        assert rv[0] == 0

    def test_stop(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        rv = th.stop_logger(mac)
        assert rv[0] == 0

    def test_ls_lid(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        rv = th.ls_lid(mac)
        _p(rv)
        assert type(rv) == dict

    def test_ls_not_lid(self):
        th = AgentBLE()
        th.start()
        th.disconnect()
        mac = '60:77:71:22:C8:18'
        rv = th.ls_not_lid(mac)
        _p(rv)
        assert type(rv) == dict

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
        _p('1st GTM {} took {}'.format(rv[1], el))
        # the next 2 are much faster
        now = time.perf_counter()
        rv = th.get_time(mac)
        assert rv[0] == 0
        rv = th.get_time(mac)
        assert rv[0] == 0
        el = time.perf_counter() - now
        _p('2nd & 3rd GTM {} took {}'.format(rv[1], el))
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
        # don't connect
        rv = th.disconnect()
        assert rv[1] == 'not agent'


