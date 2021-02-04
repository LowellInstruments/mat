import time
from mat.logger_controller_ble import FAKE_MAC_RN4020
from mat.logger_controller_ble_dummy import LoggerControllerBLEDummy, FakePer, no_cmd_in_logger


class LoggerControllerBLEDummyRN4020(LoggerControllerBLEDummy):
    def __init__(self, mac, hci_if=0):
        assert mac in [FAKE_MAC_RN4020]
        super().__init__()
        self.address = None
        self.per = FakePer(mac)
        self.type = 'dummy_rn4020'
        self.h = hci_if

    def open(self):
        # simulate some time to establish connection
        time.sleep(1)
        self.per.state = 'conn'
        self.address = self.per.addr
        self.open_post()
        return True

    def send_btc(self):
        assert self.address
        return 'CMD\r\nAOK\r\nMLDP'

    def get_file(self, file, fol, size, sig=None):
        assert self.address
        if file in self.files.keys():
            return True
        return False

    def gfv(self):
        return 'd.u.40'

    def send_cfg(self, _): return no_cmd_in_logger(self)
    def dwg_file(self, *args): return no_cmd_in_logger(self)
    def log_en(self): return no_cmd_in_logger(self)
    def mbl_en(self): return no_cmd_in_logger(self)
    def wake_en(self): return no_cmd_in_logger(self)
    def mts(self): return no_cmd_in_logger(self)
    def frm(self): return no_cmd_in_logger(self)
