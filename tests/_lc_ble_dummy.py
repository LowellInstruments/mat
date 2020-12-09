import time

from mat.logger_controller import CALIBRATION_CMD, STATUS_CMD, FIRMWARE_VERSION_CMD, SERIAL_NUMBER_CMD, TIME_CMD, \
    REQ_FILE_NAME_CMD, LOGGER_INFO_CMD, SD_FREE_SPACE_CMD, DO_SENSOR_READINGS_CMD, SENSOR_READINGS_CMD
from mat.logger_controller_ble import FAKE_MAC_CC26X2, FAKE_MAC_RN4020, LoggerControllerBLE, LOG_EN_CMD, MOBILE_CMD, \
    UP_TIME_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, BTC_CMD, CRC_CMD, FILESYSTEM_CMD, BAT_CMD, SIZ_CMD, WAKE_CMD


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
        dummy_answers_map = {
            STATUS_CMD: '0201',
            LOG_EN_CMD: '0201',
            MOBILE_CMD: '0201',
            FIRMWARE_VERSION_CMD: '1.2.34',
            SERIAL_NUMBER_CMD: '20201112',
            UP_TIME_CMD: '12345678',
            TIME_CMD: '2020/12/31 12:34:56',
            REQ_FILE_NAME_CMD: 'fake_file_name.lid',
            LOGGER_INFO_CMD: 'AAAA',
            SD_FREE_SPACE_CMD: '12345678',
            DO_SENSOR_READINGS_CMD: '111122223333',
            ERROR_WHEN_BOOT_OR_RUN_CMD: '0201',
            CALIBRATION_CMD: 'BBBBBBBB',
            SENSOR_READINGS_CMD: '0123456789012345678901234567890123456789',
            BTC_CMD: 'CMD\r\nAOK\r\nMLDP',
            CRC_CMD: 'ABCD1234',
            FILESYSTEM_CMD: 'fakefs',
            BAT_CMD: '5678',
            SIZ_CMD: '55555555',
            WAKE_CMD: '0201'
        }
        ans = dummy_answers_map.setdefault(args[0], '00')
        return args[0].encode(), ans.encode()


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
