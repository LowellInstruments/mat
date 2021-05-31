import time
from mat.logger_controller_ble import FAKE_MAC_RN4020
from mat.logger_controller_ble_dummy import LoggerControllerBLEDummy, FakePer, no_cmd_in_logger


class LoggerControllerBLEDummyRN4020(LoggerControllerBLEDummy):
    def __init__(self, mac, hci_if=0):
        assert mac == FAKE_MAC_RN4020
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

    def gfv(self): return 'd.u.40'

    def frm(self): return no_cmd_in_logger(self)
    def log_en(self): return no_cmd_in_logger(self)
    def mbl_en(self): return no_cmd_in_logger(self)
    def wake_en(self): return no_cmd_in_logger(self)
    def mts(self): return no_cmd_in_logger(self)
    def dwg_file(self, *args): return no_cmd_in_logger(self)
    def send_cfg(self, _): return no_cmd_in_logger(self)
    def crc_file(self, name): return no_cmd_in_logger(self)


