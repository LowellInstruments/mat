import time
from mat.logger_controller_ble import FAKE_MAC_CC26X2, FAKE_MAC_RN4020, LoggerControllerBLE


class FakePer:
    def __init__(self):
        self.state = 'disc'

    def getState(self):
        return self.state


class LoggerControllerBLEDummy(LoggerControllerBLE):
    def __init__(self, mac):
        super().__init__(mac)
        # self.address is set by specific constructor
        self.address = None
        self.per = FakePer()

    def open(self):
        print('puta')
        pass

    def open_post(self):
        assert self.address

    def ble_write(self, data, response=False):
        assert self.address

    def get_file(self, file, fol, size, sig=None):
        assert self.address
        return True

    def get_type(self):
        assert self.address
        return self.type

    def close(self):
        self.per.state = 'disc'
        self.type = None
        self.address = False
        return True

    def purge(self):
        assert self.address

    def xmd_rx_n_save(self, *args):
        assert self.address
        return True

    def get_time(self):
        assert self.address
        return '2020/12/31 12:34:56'

    def send_cfg(self, _):
        assert self.address
        return [b'CFG', b'00']

    def dwg_file(self, *args):
        assert self.address
        return True

    def ls_lid(self):
        assert self.address
        return {'a.lid': '1234'}

    def ls_not_lid(self):
        assert self.address
        return {'MAT.cfg': '101'}

    def command(self, *args):
        # first version
        assert self.address
        return args[0].encode(), b'00'


class LoggerControllerBLEDummyCC26x2(LoggerControllerBLEDummy):
    def __init__(self, mac):
        assert mac == FAKE_MAC_CC26X2
        super().__init__(mac)
        self.type = 'cc26x2'

    def open(self):
        # simulate some time to establish connection
        time.sleep(1)
        self.per.state = 'conn'
        self.address = FAKE_MAC_CC26X2
        self.open_post()
        return True

    def send_btc(self):
        # does not exist for CC26X2 loggers
        assert self.address
        return False


class LoggerControllerBLEDummyRN4020(LoggerControllerBLEDummy):
    def __init__(self, mac):
        assert mac == FAKE_MAC_RN4020
        super().__init__(mac)
        self.type = 'rn4020'

    def open(self):
        # simulate some time to establish connection
        time.sleep(1)
        self.per.state = 'conn'
        self.address = FAKE_MAC_RN4020
        self.open_post()
        return True

    def send_cfg(self, _):
        # does not exist for RN4020 loggers
        assert self.address
        return False

    def dwg_file(self, *args):
        # does not exist for RN4020 loggers
        assert self.address
        return False

    def send_btc(self):
        assert self.address
        return 'BTC 00T,0006,0000,0064'
