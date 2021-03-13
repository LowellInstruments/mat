import time
from mat.logger_controller_ble import FAKE_MAC_CC26X2, CONFIG_CMD, CRC_CMD
from mat.logger_controller_ble_dummy import LoggerControllerBLEDummy, FakePer, no_cmd_in_logger


class LoggerControllerBLEDummyCC26x2(LoggerControllerBLEDummy):
    def __init__(self, mac, hci_if=0):
        assert mac in [FAKE_MAC_CC26X2]
        super().__init__()
        self.address = None
        self.per = FakePer(mac)
        self.type = 'dummy_cc26x2'
        self.h = hci_if

    def open(self):
        # simulate some time to establish connection
        time.sleep(1)
        self.per.state = 'conn'
        self.address = self.per.addr
        self.open_post()
        return True

    def log_en(self):
        key = 'log_enabled_or_disabled'
        self.fake_state[key] ^= 1
        return '01' if self.fake_state[key] else '00'

    def mbl_en(self):
        key = 'mbl_enabled_or_disabled'
        self.fake_state[key] ^= 1
        return '01' if self.fake_state[key] else '00'

    def wake_en(self):
        key = 'wake_enabled_or_disabled'
        self.fake_state[key] ^= 1
        return '01' if self.fake_state[key] else '00'

    def mts(self):
        _t = str(int(time.perf_counter()))
        name = 'data_{}.lid'.format(_t)
        size = _t[-4:]
        self.files[name] = size
        # '' becomes a command() return value of '00'
        return ''

    def gfv(self):
        return 'd.u.26'

    def get_file(self, file, fol, size, sig=None):
        assert self.address
        if file not in self.files.keys():
            return False
        path = '{}/{}'.format(fol, file)

        # asking for MAT.cfg file
        if file == 'MAT.cfg':
            with open(path, 'w') as f:
                s = '{ "fruit": "Apple" }'
                f.write(s)
            return True

        # when asking for files not MAT.cfg
        with open(path, 'w') as f:
            f.write('*' * int(size))
        return True

    def frm(self):
        self.files = {}
        return ''

    def dwg_file(self, *args):
        # re-use
        file, fol, size, sig = args
        return self.get_file(file, fol, size, sig)

    def send_cfg(self, _):
        return [b'CFG', b'00']

    def send_btc(self):
        return no_cmd_in_logger(self)

    def crc_file(self, name) -> str:
        crc_dict = {
            'a.lid': 'AD5472CC',
            'b.lid': '58373920',
            'MAT.cfg': '62524C09'
        }
        return crc_dict[name]
