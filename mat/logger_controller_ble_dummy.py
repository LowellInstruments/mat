import datetime
import time
import types
from abc import abstractmethod

from bluepy.btle import BTLEException

from mat.logger_controller import CALIBRATION_CMD, STATUS_CMD, FIRMWARE_VERSION_CMD, SERIAL_NUMBER_CMD, TIME_CMD, \
    REQ_FILE_NAME_CMD, LOGGER_INFO_CMD, SD_FREE_SPACE_CMD, DO_SENSOR_READINGS_CMD, SENSOR_READINGS_CMD, RUN_CMD, \
    STOP_CMD, RWS_CMD, SWS_CMD, DEL_FILE_CMD
from mat.logger_controller_ble import LOG_EN_CMD, MOBILE_CMD, \
    UP_TIME_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, BTC_CMD, CRC_CMD, FILESYSTEM_CMD, BAT_CMD, SIZ_CMD, WAKE_CMD, \
    ERR_MAT_ANS, MY_TOOL_SET_CMD, FORMAT_CMD, GET_FILE_CMD, CONFIG_CMD

# to test exception / notification generation
EXC_CMD = 'EXC'


class FakePer:
    def __init__(self, mac):
        self.state = 'disc'
        self.addr = mac

    def getState(self):
        return self.state


class LoggerControllerBLEDummy:
    def __init__(self):
        # MAC address set by specific constructor
        self.fake_state = {
            'running_or_stopped': 0,
            'log_enabled_or_disabled': 0,
            'mbl_enabled_or_disabled': 0,
            'wake_enabled_or_disabled': 0
        }
        self.files = {
            'a.lid': '1234',
            'b.lid': '5678',
            'MAT.cfg': '101'
        }

    @abstractmethod
    def open(self): pass

    @abstractmethod
    def log_en(self): pass

    @abstractmethod
    def gfv(self): pass

    @abstractmethod
    def crc_file(self, name): pass

    @abstractmethod
    def mbl_en(self): pass

    @abstractmethod
    def mts(self): pass

    @abstractmethod
    def get_file(self, file, fol, size, sig=None): pass

    @abstractmethod
    def send_btc(self): pass

    @abstractmethod
    def dwg_file(self, *args): pass

    @abstractmethod
    def frm(self): pass

    @abstractmethod
    def wake_en(self): pass

    def open_post(self):
        assert self.address

    def ble_write(self, data, response=False):
        assert self.address

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
        # this is not GTM command
        assert self.address
        # careful to make this comply with tests
        return datetime.datetime.now()

    def sync_time(self):
        assert self.address
        return [b'STM', b'00']

    def exc_test(self):
        # to test connectivity lost
        raise BTLEException('exc_test')

    def ls_lid(self):
        assert self.address
        _d = {k: v for k, v in self.files.items() if '.lid' in k}
        return _d

    def ls_not_lid(self):
        assert self.address
        _d = {k: v for k, v in self.files.items() if '.lid' not in k}
        return _d

    def ls_ext(self, ext):
        assert self.address
        ext = ext.decode() if type(ext) == bytes else ext
        _d = {k: v for k, v in self.files.items() if k.endswith(ext)}
        return _d

    def del_file(self, name):
        assert self.address
        if name in self.files.keys():
            del self.files[name]
        return ''

    def gsr_do(self):
        assert self.address
        # simulate IN-situ brand sensor time to measure
        time.sleep(3)
        return '111122223333'

    def sts(self):
        key = 'running_or_stopped'
        # recall rv '01' means stopped
        return '00' if self.fake_state[key] else '01'

    def stop(self):
        key = 'running_or_stopped'
        self.fake_state[key] = 0
        return ''

    def gtm(self):
        a = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        a = '19{}'.format(a)
        return [b'STM', a.encode()]

    def run(self, s=''):
        key = 'running_or_stopped'
        if self.fake_state[key]:
            return ERR_MAT_ANS
        self.fake_state[key] = 1
        return ''

    def command(self, *args):
        # args: ('DEL', 'a.lid')command
        assert self.address
        _c = args[0]
        dummy_answers_map = {
            STATUS_CMD: self.sts,
            LOG_EN_CMD: self.log_en,
            MOBILE_CMD: self.mbl_en,
            FIRMWARE_VERSION_CMD: self.gfv,
            SERIAL_NUMBER_CMD: 'AAAAAAA',
            UP_TIME_CMD: '100e0000',    # 1h = 0x0000e010
            REQ_FILE_NAME_CMD: 'fake_file_name.lid',
            SD_FREE_SPACE_CMD: '00000040',  # 64 MB = 0x400000000
            DO_SENSOR_READINGS_CMD: self.gsr_do,
            ERROR_WHEN_BOOT_OR_RUN_CMD: '01',
            CALIBRATION_CMD: 'BBBBBBBB',
            SENSOR_READINGS_CMD: '0123456789' * 4,
            BTC_CMD: self.send_btc,
            CRC_CMD: self.crc_file,
            FILESYSTEM_CMD: 'fakefs',
            BAT_CMD: '5678',
            SIZ_CMD: '9876',
            WAKE_CMD: self.wake_en,
            RUN_CMD: self.run,
            STOP_CMD: self.stop,
            RWS_CMD: self.run,
            SWS_CMD: self.stop,
            LOGGER_INFO_CMD: 'AAAAAAA',
            MY_TOOL_SET_CMD: self.mts,
            DEL_FILE_CMD: self.del_file,
            FORMAT_CMD: self.frm,
            GET_FILE_CMD: self.get_file,
            TIME_CMD: self.gtm,
            EXC_CMD: self.exc_test,
            # CONFIG_CMD not here bc not sent w/ command()
        }
        # default: commands not needing to check anything
        _a = dummy_answers_map.setdefault(args[0], '')
        if isinstance(_a, types.MethodType):
            _a = _a(args[1]) if len(args) > 1 else _a()

        # in case answer gives error
        if _a == ERR_MAT_ANS.encode():
            return ERR_MAT_ANS.encode()

        # add hex length prefix
        _a = '{:02x}{}'.format(len(_a), _a) if len(_a) else '00'
        rv = [args[0].encode(), _a.encode()]
        return rv

    def __enter__(self):
        if self.open():
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def no_cmd_in_logger(lc):
    # does not exist for this type of logger
    assert lc.address
    return ERR_MAT_ANS.encode()