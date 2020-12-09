import time
import types
from abc import ABC, abstractmethod

from mat.logger_controller import CALIBRATION_CMD, STATUS_CMD, FIRMWARE_VERSION_CMD, SERIAL_NUMBER_CMD, TIME_CMD, \
    REQ_FILE_NAME_CMD, LOGGER_INFO_CMD, SD_FREE_SPACE_CMD, DO_SENSOR_READINGS_CMD, SENSOR_READINGS_CMD, RUN_CMD, \
    STOP_CMD, RWS_CMD, SWS_CMD
from mat.logger_controller_ble import LoggerControllerBLE, LOG_EN_CMD, MOBILE_CMD, \
    UP_TIME_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, BTC_CMD, CRC_CMD, FILESYSTEM_CMD, BAT_CMD, SIZ_CMD, WAKE_CMD, \
    FAKE_MAC_CC26X2, FAKE_MAC_RN4020, ERR_MAT_ANS, CONFIG_CMD

FAKE_TIME = '2020/12/31 12:34:56'


class FakePer:
    def __init__(self):
        self.state = 'disc'

    def getState(self):
        return self.state


class LoggerControllerBLEDummy(LoggerControllerBLE, ABC):
    def __init__(self, mac):
        super().__init__(mac)
        # self.address is set by specific constructor
        self.address = None
        self.per = FakePer()
        self.fake_state = {
            'running_or_stopped': 0,
            'log_enabled_or_disabled': 0,
            'mbl_enabled_or_disabled': 0,
            'wake_enabled_or_disabled': 0
        }

    @abstractmethod
    def open(self): pass

    @abstractmethod
    def send_cfg(self, _): pass

    @abstractmethod
    def log_en(self): pass

    @abstractmethod
    def mbl_en(self): pass

    @abstractmethod
    def send_btc(self): pass

    @abstractmethod
    def dwg_file(self, *args): pass

    @abstractmethod
    def wake_en(self): pass

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
        return FAKE_TIME

    def ls_lid(self):
        assert self.address
        return {'a.lid': '1234'}

    def ls_not_lid(self):
        assert self.address
        return {'MAT.cfg': '101'}

    def gsr_do(self):
        assert self.address
        # simulate IN-situ brand sensor time to measure
        time.sleep(3)
        return '111122223333'

    def sts(self):
        key = 'running_or_stopped'
        return '01' if self.fake_state[key] else '00'

    def toggle_run(self):
        key = 'running_or_stopped'
        self.fake_state[key] ^= 1
        return '01' if self.fake_state[key] else '00'

    def command(self, *args):
        # only commands rv != b'00' and particular ones
        assert self.address
        _c = args[0]
        dummy_answers_map = {
            STATUS_CMD: self.sts,
            LOG_EN_CMD: self.log_en,
            MOBILE_CMD: self.mbl_en,
            FIRMWARE_VERSION_CMD: '1.2.34',
            SERIAL_NUMBER_CMD: '20201112',
            UP_TIME_CMD: '100e0000',    # 1h = 0x100e0000
            TIME_CMD: FAKE_TIME,
            REQ_FILE_NAME_CMD: 'fake_file_name.lid',
            SD_FREE_SPACE_CMD: '12345678',
            DO_SENSOR_READINGS_CMD: self.gsr_do,
            ERROR_WHEN_BOOT_OR_RUN_CMD: '01',
            CALIBRATION_CMD: 'BBBBBBBB',
            SENSOR_READINGS_CMD: '0123456789012345678901234567890123456789',
            BTC_CMD: self.send_btc,
            CRC_CMD: 'ABCD1234',
            FILESYSTEM_CMD: 'fakefs',
            BAT_CMD: '5678',
            SIZ_CMD: '9876',
            WAKE_CMD: self.wake_en,
            CONFIG_CMD: self.send_cfg,
            RUN_CMD: self.toggle_run,
            STOP_CMD: self.toggle_run,
            RWS_CMD: self.toggle_run,
            SWS_CMD: self.toggle_run,
            LOGGER_INFO_CMD: 'AAAAAAA',
        }
        _a = dummy_answers_map.setdefault(args[0], '00')
        if isinstance(_a, types.MethodType):
            _a = _a()

        # todo: does this work?
        _a = '{:02x}{}'.format(len(_a), _a)
        rv = [args[0].encode(), _a.encode()]
        return rv


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

    def dwg_file(self, *args):
        return True

    def send_cfg(self, _):
        return [b'CFG', b'00']

    def send_btc(self):
        return no_cmd_in_logger(self)


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

    def send_btc(self):
        assert self.address
        return 'CMD\r\nAOK\r\nMLDP'

    def send_cfg(self, _):
        return no_cmd_in_logger(self)

    def dwg_file(self, *args):
        return no_cmd_in_logger(self)

    def log_en(self):
        return no_cmd_in_logger(self)

    def mbl_en(self):
        return no_cmd_in_logger(self)

    def wake_en(self):
        return no_cmd_in_logger(self)


def no_cmd_in_logger(lc):
    # does not exist for this type of logger
    assert lc.address
    return ERR_MAT_ANS.encode()
