import re
import bluepy.btle as ble
import json
from datetime import datetime
import time
from mat.logger_controller import LoggerController, STATUS_CMD, STOP_CMD, DO_SENSOR_READINGS_CMD, TIME_CMD, \
    FIRMWARE_VERSION_CMD, SERIAL_NUMBER_CMD, REQ_FILE_NAME_CMD, LOGGER_INFO_CMD, RUN_CMD, RWS_CMD, SD_FREE_SPACE_CMD, \
    SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, LOGGER_INFO_CMD_W, DIR_CMD, CALIBRATION_CMD, RESET_CMD, SENSOR_READINGS_CMD, \
    LOGGER_HSA_CMD_W
from mat.logger_controller_ble_cc26x2 import LoggerControllerBLECC26X2
from mat.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.utils import linux_is_docker
from mat.xmodem_ble_cc26x2 import xmd_get_file_cc26x2, XModemException
import pathlib
import subprocess as sp
from mat.xmodem_ble_rn4020 import xmd_get_file_rn4020


FAKE_MAC_CC26X2 = 'xx:cc:26:x2:ff:ff'
FAKE_MAC_RN4020 = 'xx:rn:40:20:ff:ff'


# commands not present in USB loggers
SIZ_CMD = 'SIZ'
BAT_CMD = 'BAT'
BTC_CMD = 'BTC'
MOBILE_CMD = 'MBL'
HW_TEST_CMD = '#T1'
FORMAT_CMD = 'FRM'
CONFIG_CMD = 'CFG'
UP_TIME_CMD = 'UTM'
MY_TOOL_SET_CMD = 'MTS'
LOG_EN_CMD = 'LOG'
WAKE_CMD = 'WAK'
ERROR_WHEN_BOOT_OR_RUN_CMD = 'EBR'
CRC_CMD = 'CRC'
FILESYSTEM_CMD = 'FIS'
_DEBUG_THIS_MODULE = 0
ERR_MAT_ANS = 'ERR'
GET_FILE_CMD = 'GET'
DWG_FILE_CMD = 'DWG'
LED_CMD = 'LED'


# constants for when trying to BLE connect
BLE_CONNECTION_RETRIES = 3
BLE_CONNECTION_TIMEOUT = 10
BLE_DISCONNECTION_TIME = 2


class Delegate(ble.DefaultDelegate):
    def __init__(self):
        ble.DefaultDelegate.__init__(self)
        self.buf = bytes()
        self.x_buf = bytes()
        self.file_mode = False

    def handleNotification(self, c_handle, data):
        if not self.file_mode:
            self.buf += data
        else:
            self.x_buf += data

    def clr_buf(self):
        self.buf = bytes()

    def clr_x_buf(self):
        self.x_buf = bytes()

    def set_file_mode(self, state):
        self.file_mode = state


class LoggerControllerBLE(LoggerController):

    def __init__(self, mac, hci_if=0):
        # checks for bad or dummy mac addresses
        assert is_valid_mac_address(mac)

        # default are (24, 40, 0)
        w_ble_linux_pars(6, 11, 0, hci_if)
        super().__init__(mac)
        self.address = mac
        self.hci_if = hci_if
        self.per = None
        self.svc = None
        self.cha = None
        self.type = None

        # set underlying BLE class
        if brand_ti(mac):
            self.und = LoggerControllerBLECC26X2(self)
        else:
            self.und = LoggerControllerBLERN4020(self)

        self.dlg = Delegate()

    def get_type(self):
        return self.und.type

    def open(self):
        for i in range(BLE_CONNECTION_RETRIES):
            try:
                self.per = ble.Peripheral(self.address, iface=self.hci_if,
                                          timeout=BLE_CONNECTION_TIMEOUT)
                # connection update request from cc26x2 takes 1000 ms
                time.sleep(1.1)
                self.per.setDelegate(self.dlg)
                self.svc = self.per.getServiceByUUID(self.und.UUID_S)
                self.cha = self.svc.getCharacteristics(self.und.UUID_C)[0]
                desc = self.cha.valHandle + 1
                self.per.writeCharacteristic(desc, b'\x01\x00')

                # first time on unknown logger, ensure BLE parameters applied
                if not is_connection_recent(self.address):  # pragma: no cover
                    self.per.disconnect()
                    continue

                self.open_post()
                return True

            except (AttributeError, ble.BTLEException) as exc:
                e = 'failed connection attempt {}/{}: {}'
                print(e.format(i + 1, BLE_CONNECTION_RETRIES, exc))
        return False

    def ble_write(self, data, response=False):  # pragma: no cover
        self.und.ble_write(data, response)

    def open_post(self):
        self.und.open_post()

    def close(self):
        try:
            self.per.disconnect()
            self.per = None
            return True
        except AttributeError:
            return False

    def _ans_is_finished(self, tag):  # pragma: no cover
        """ ends last command sent answer timeout """

        b = self.dlg.buf

        # useful when debugging
        # if b:
        #     print(b)

        # ex: rn4020 b'\r\n\n\rSTS 0201\r\n', cc26x2 b'\STS 0201'
        if self.und.type == 'rn4020':
            b = b.strip()

        try:
            # answer bytes -> string
            a = b.decode()
        except UnicodeError:
            # DWL answer remains bytes
            tag = 'DWL'
            a = b

        # early leave when error or invalid command
        if a.startswith(ERR_MAT_ANS) or a.startswith('INV'):
            time.sleep(.5)
            return True

        # (partial) answer, check it
        return _ans_check(tag, a, b)

    def _wait_answer_to_ble_cmd(self, tag: str):    # pragma: no cover
        w = calc_ble_cmd_ans_timeout(tag)
        till = time.perf_counter() + w
        while 1:
            if time.perf_counter() > till:
                break
            if self._ans_is_finished(tag):
                break
            if self.per.waitForNotifications(0.001):
                till += 0.001
        # e.g. b'' / b'STS 00'
        return self.dlg.buf

    def purge(self):   # pragma: no cover
        self.dlg.clr_buf()
        self.dlg.clr_x_buf()

    def command(self, *args):   # pragma: no cover
        self.purge()
        self.dlg.set_file_mode(False)

        # phone commands in aggregated, a.k.a. transparent, mode
        tp_mode = len(str(args[0]).split(' ')) > 1

        # build ASCII command
        cmd = str(args[0])
        if tp_mode:
            to_send = cmd
        else:
            cmd = str(args[0])
            arg = str(args[1]) if len(args) == 2 else ''
            n = '{:02x}'.format(len(arg)) if arg else ''
            to_send = cmd + ' ' + n + arg
        to_send += chr(13)

        # obtain command tag
        tag = cmd[:3]
        _cmd_pre_slow_down_if_so(tag)

        # send command, wait answer
        self.ble_write(to_send.encode())
        ans = self._wait_answer_to_ble_cmd(tag).split()

        # pause a bit, if so
        _cmd_post_slow_down_if_so(tag)

        # e.g. [b'STS', b'020X']
        return ans

    def flood(self, n):   # pragma: no cover
        """ attack test: sends command burst w/o caring answers """
        for i in range(n):
            cmd = STATUS_CMD
            cmd += chr(13)
            self.ble_write(cmd.encode())

    def xmd_rx_n_save(self, file, fol, size, sig=None):   # pragma: no cover
        """ called after _get_file(), downloads file w/ x-modem """
        fxn_map = {
            'cc26x2': xmd_get_file_cc26x2,
            'rn4020': xmd_get_file_rn4020
        }
        xmd_fxn = fxn_map[self.und.type]

        self.dlg.set_file_mode(True)
        try:
            rv, data = xmd_fxn(self, sig, verbose=False)
        except XModemException:
            rv, data = False, None
        finally:
            self.dlg.set_file_mode(False)

        if not rv or len(data) < int(size):
            return False
        p = '{}/{}'.format(fol, file)
        with open(p, 'wb') as f:
            f.write(data)
            f.truncate(int(size))
        return True

    def get_file(self, file, fol, size, sig=None):  # pragma: no cover
        rv = False
        try:
            rv = self.und.get_file(self, file, fol, size, sig)
        except ble.BTLEException as ex:
            # show this exception, app will take care of it
            # and / or next BLE command will nicely fail
            print('BLE: get_file() exception {}'.format(ex))
        finally:
            self.dlg.set_file_mode(False)
            return rv

    def get_time(self):
        ans = self.command(TIME_CMD)
        if not ans:
            return
        try:
            _time = ans[1].decode()[2:] + ' '
            _time += ans[2].decode()
            # this returns a datetime object
            return datetime.strptime(_time, '%Y/%m/%d %H:%M:%S')
        except (ValueError, IndexError):
            print('BLE: get_time() malformed: {}'.format(ans))

    # wrapper for DIR command
    def _ls(self):
        rv = []

        for i in range(5):
            rv = self.command(DIR_CMD)
            # ensure DIR answer is clean
            self.command(STATUS_CMD)
            self.command(STATUS_CMD)
            if rv:
                break
            s = 'BLE: DIR empty, retry {} of 5'.format(i)
            print(s)
            time.sleep(2)

        # e.g. [b'.', b'0', b'..', b'0', b'dummy.lid', b'123', b'\x04']
        return rv

    def ls_ext(self, ext):  # pragma: no cover
        return _ls_wildcard(self._ls(), ext, match=True)

    def ls_lid(self):
        ext = b'lid'
        return _ls_wildcard(self._ls(), ext, match=True)

    def ls_not_lid(self):
        ext = b'lid'
        return _ls_wildcard(self._ls(), ext, match=False)

    def send_cfg(self, cfg_d: dict):  # pragma: no cover
        s = json.dumps(cfg_d)
        return self.command(CONFIG_CMD, s)

    def send_btc(self):
        """ only on RN4020-based loggers: set fast mode """
        if self.und.type == 'rn4020':
            s = 'BTC 00T,0006,0000,0064'
            _ = self.command(s)
            return _
        else:
            return 'wrong logger type'

    def _dwl_chunk_loop(self, sig, data):   # pragma: no cover
        """ accumulate on data parameter """
        last = time.perf_counter()
        while 1:
            if self.per.waitForNotifications(.1):
                last = time.perf_counter()
            if time.perf_counter() > last + 2:
                # do not forget the remaining bytes < 2048
                data += self.dlg.x_buf
                return True, data
            if len(self.dlg.x_buf) >= 2048:
                data += self.dlg.x_buf[:2048]
                self.dlg.x_buf = self.dlg.x_buf[2048:]
                if sig:
                    sig.emit()
                return False, data

    def _dwl_file(self, size, sig=None):   # pragma: no cover
        """ XMODEM equivalent, called by dwg_file() """
        self.dlg.set_file_mode(True)
        data = bytes()
        self.dlg.x_buf = bytes()

        # download chunk by chunk
        c_n = 0
        while 1:
            cmd = 'DWL {:02x}{}\r'.format(len(str(c_n)), c_n)
            c_n += 1
            self.ble_write(cmd.encode())
            # a DWL timeout does not mean failure, also end of file
            timeout, data = self._dwl_chunk_loop(sig, data)
            if timeout or len(data) >= int(size):
                break

        # clean-up
        self.dlg.set_file_mode(False)
        self.dlg.x_buf = bytes()

        return data

    def dwg_file(self, file, fol, size, sig=None) -> bool:  # pragma: no cover
        data = None

        try:
            _ = '{} {:02x}{}\r'
            cmd = _.format(DWG_FILE_CMD, len(file), file)
            self.ble_write(cmd.encode())
            self.per.waitForNotifications(10)
            if self.dlg.buf and self.dlg.buf.endswith(b'DWG 00'):
                data = self._dwl_file(size, sig)
                if data and len(data) == int(size):
                    path = '{}/{}'.format(fol, file)
                    with open(path, 'wb') as f:
                        f.write(data)
                        f.truncate(int(size))
                else:
                    data = None
            else:
                e = 'DBG: dwg_file() error, self.dlg.buf -> {}'
                print(e.format(self.dlg.buf))

        except ble.BTLEException as ex:
            # show this exception, app will take care of it
            # and / or next BLE command will nicely fail
            print('BLE: dwg_file() exception {}'.format(ex))

        return data


# utilities
def _ls_wildcard(lis, ext, match=True):
    if lis is None:
        return {}

    err = ERR_MAT_ANS.encode()
    if err in lis:
        return err

    files, idx = {}, 0
    while idx < len(lis):
        name = lis[idx]
        if name in [b'\x04']:
            break
        if name.endswith(ext) == match and name not in [b'.', b'..']:
            files[name.decode()] = int(lis[idx + 1])
        idx += 2
    return files


def brand_ti(mac):
    mac = mac.lower()
    return not brand_microchip(mac)


def brand_microchip(mac):
    mac = mac.lower()
    return mac.startswith('00:1e:c0:') or mac == FAKE_MAC_RN4020


def ble_scan(hci_if: int, my_to=3.0):    # pragma: no cover
    # hci_if: hciX interface number
    import sys
    try:
        s = ble.Scanner(iface=hci_if)
        # it'd seem external Bluetooth dongles need passive
        _p = True if hci_if else False
        return s.scan(timeout=my_to, passive=_p)
    except OverflowError:
        e = 'SYS: overflow on BLE scan, maybe date time error'
        print(e)
        sys.exit(1)


def is_connection_recent(mac):  # pragma: no cover
    # /dev/shm is cleared every reboot
    mac = str(mac).replace(':', '')
    path = pathlib.Path('/dev/shm/{}'.format(mac))
    if path.exists():
        return True
    path.touch()
    return False


def _r_ble_linux_pars(banner, hci_if: int) -> (int, int, int):   # pragma: no cover
    min_ce = '/sys/kernel/debug/bluetooth/hci{}/conn_min_interval'
    max_ce = '/sys/kernel/debug/bluetooth/hci{}/conn_max_interval'
    lat = '/sys/kernel/debug/bluetooth/hci{}/conn_latency'
    min_ce = min_ce.format(hci_if)
    max_ce = max_ce.format(hci_if)
    lat = lat.format(hci_if)

    # must match bind mount points in docker invoking
    if linux_is_docker():
        min_ce = '/_{}'.format(min_ce[1:])
        max_ce = '/_{}'.format(max_ce[1:])
        lat = '/_{}'.format(lat[1:])
        print('DDH Docker inherits BLE host connection parameters')

    try:
        with open(min_ce, 'r') as _:
            l1 = _.readline().rstrip('\n')
        with open(max_ce, 'r') as _:
            l2 = _.readline().rstrip('\n')
        with open(lat, 'r') as _:
            l3 = _.readline().rstrip('\n')
        print('{} R linux BLE pars {}'.format(banner, (l1, l2, l3)))
        return int(l1), int(l2), int(l3)
    except FileNotFoundError:
        print('can\'t read /sys/kernel/bluetooth')


def w_ble_linux_pars(l1, l2, l3, hci_if: int):   # pragma: no cover
    # order is important
    _r_ble_linux_pars('pre:', hci_if)

    min_ce = '/sys/kernel/debug/bluetooth/hci{}/conn_min_interval'
    max_ce = '/sys/kernel/debug/bluetooth/hci{}/conn_max_interval'
    lat = '/sys/kernel/debug/bluetooth/hci{}/conn_latency'
    min_ce = min_ce.format(hci_if)
    max_ce = max_ce.format(hci_if)
    lat = lat.format(hci_if)

    # must match bind mount points in docker invoking
    if linux_is_docker():
        min_ce = '/_{}'.format(min_ce[1:])
        max_ce = '/_{}'.format(max_ce[1:])
        lat = '/_{}'.format(lat[1:])
        print('DDH Docker inherits BLE host connection parameters')

    try:
        c = 'echo {} > {}'.format(l2, max_ce)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(l1, min_ce)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(l3, lat)
        sp.run(c, shell=True, check=True)
        assert _r_ble_linux_pars('post:', hci_if) == (l1, l2, l3)
        return
    except sp.CalledProcessError:
        pass
    try:
        # invert order
        c = 'echo {} > {}'.format(l1, min_ce)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(l2, max_ce)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(l3, lat)
        sp.run(c, shell=True, check=True)
        assert _r_ble_linux_pars('post:', hci_if) == (l1, l2, l3)
        return
    except sp.CalledProcessError:
        pass


def is_a_li_logger(rd):
    """
    identifies lowell instruments' loggers
    :param rd: bluepy Scanner.scan() rawData object
    """
    if type(rd) is not bytes:
        return False
    known_li_types = [b'DO-1',
                      b'MATP-2W',
                      b'MAT-2W']
    for _ in known_li_types:
        if _ in bytes(rd):
            return True
    return False


def _ans_check(tag, a, b):
    # helper: function expects a 'TAG 00' answer when z is 0
    def _exp(fixed=0):
        _ = '{} 00'.format(tag) if fixed else tag
        return a.startswith(_)

    # a command stops timeout, early leaves (el) when getting proper answer
    _el = {
        DIR_CMD: lambda: b.endswith(b'\x04\n\r') or b.endswith(b'\x04'),
        STATUS_CMD: lambda: _exp() and len(a) == 8,
        LOG_EN_CMD: lambda: _exp() and len(a) == 8,
        MOBILE_CMD: lambda: _exp() and len(a) == 8,
        FIRMWARE_VERSION_CMD: lambda: _exp() and len(a) == 6 + 6,
        SERIAL_NUMBER_CMD: lambda: _exp() and len(a) == 6 + 7,
        UP_TIME_CMD: lambda: _exp(),
        TIME_CMD: lambda: _exp() and len(a) == 6 + 19,
        SET_TIME_CMD: lambda: _exp(1),
        RUN_CMD: lambda: _exp(1),
        LED_CMD: lambda: _exp(1),
        # rn4020 b'STP 0200', cc26x2 b'STP 00'
        STOP_CMD: lambda: _exp(1) or (_exp(0) and len(a) == 8),
        RWS_CMD: lambda: _exp(1),
        SWS_CMD: lambda: _exp(1),
        REQ_FILE_NAME_CMD: lambda: _exp(1) or a.endswith('.lid'),
        LOGGER_INFO_CMD: lambda: _exp() and len(a) <= 6 + 7,
        LOGGER_INFO_CMD_W: lambda: _exp(1),
        SD_FREE_SPACE_CMD: lambda: _exp() and len(a) == 6 + 8,
        CONFIG_CMD: lambda: _exp(1),
        DEL_FILE_CMD: lambda: _exp(1),
        MY_TOOL_SET_CMD: lambda: _exp(1),
        DO_SENSOR_READINGS_CMD: lambda: _exp() and (len(a) == 6 + 12),
        FORMAT_CMD: lambda: _exp(1),
        ERROR_WHEN_BOOT_OR_RUN_CMD: lambda: _exp() and (len(a) == 6 + 5),
        CALIBRATION_CMD: lambda: _exp() and (len(a) == 6 + 8),
        RESET_CMD: lambda: _exp(1),
        SENSOR_READINGS_CMD: lambda: _exp() and (len(a) == 6 + 40),
        BTC_CMD: lambda: b == b'CMD\r\nAOK\r\nMLDP',
        CRC_CMD: lambda: _exp() and (len(a) == 6 + 8),
        FILESYSTEM_CMD: lambda: a in ['littlefs', 'spiffs'],
        BAT_CMD: lambda: _exp() and (len(a) == 6 + 4),
        SIZ_CMD: lambda: _exp() and (6 + 1 <= len(a) <= 6 + 10),
        WAKE_CMD: lambda: _exp() and len(a) == 8,
        LOGGER_HSA_CMD_W: lambda: _exp(1)
        # GET_FILE_CMD and DWG_FILE_CMD done elsewhere
    }
    _el.setdefault(tag, lambda: _ans_unk(tag))
    return _el[tag]()


def _cmd_pre_slow_down_if_so(tag):
    """ ensure commands are spaced """
    _st = {
        CRC_CMD: 2,
        FORMAT_CMD: 2
    }

    # 0 means no extra pre slow down
    t = _st.setdefault(tag, 0)
    if t:
        s = '- dbg: pre_slow_down for {} is {} -'
        # print(s.format(tag, t))
        time.sleep(t)


def _cmd_post_slow_down_if_so(tag: str):
    """ after answer received or timeout expired """
    _st = {
        LOGGER_INFO_CMD: .1,
        LOGGER_INFO_CMD_W: .1,
        CONFIG_CMD: 1.5,
        RUN_CMD: 1,
        STOP_CMD: 1,
        RWS_CMD: 1,
        SWS_CMD: 1,
    }

    # 0 means no extra slow down
    t = _st.setdefault(tag, 0)
    time.sleep(t)


# helper: function returns false if tag is unknown
def _ans_unk(_tag):  # pragma: no cover
    print('unknown tag {}'.format(_tag))
    return False


# can be called by ClientN2LH
def calc_ble_cmd_ans_timeout(tag):
    _timeouts = {
        RUN_CMD: 50,
        RWS_CMD: 50,
        CRC_CMD: 20,
        # NOR memories have Write, Erase slow
        FORMAT_CMD: 60,
        MY_TOOL_SET_CMD: 30,
        DO_SENSOR_READINGS_CMD: 4,
    }
    t = _timeouts.setdefault(tag, 10)
    return t


def is_valid_mac_address(mac):
    if mac in [FAKE_MAC_CC26X2, FAKE_MAC_RN4020]:
        return True

    # src: geeks for geeks website
    regex = ("^([0-9A-Fa-f]{2}[:])" +
        "{5}([0-9A-Fa-f]{2})|" +
        "([0-9a-fA-F]{4}\\." +
        "[0-9a-fA-F]{4}\\." +
        "[0-9a-fA-F]{4})$")

    p = re.compile(regex)
    if mac is None:
        return False

    if re.search(p, mac):
        return True
    else:
        return False


def get_logger_type_by_mac(mac):
    if mac.startswith(FAKE_MAC_CC26X2[:12]):
        return 'dummy_cc26x2'
    if mac.startswith(FAKE_MAC_RN4020[:12]):
        return 'dummy_rn4020'
    if brand_microchip(mac):
        return 'rn4020'
    if brand_ti(mac):
        return 'cc26x2'
    return 'unknown_type'

