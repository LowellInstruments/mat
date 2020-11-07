import bluepy.btle as ble
import json
from datetime import datetime
import time
from mat.linux import linux_is_docker
from mat.logger_controller import LoggerController, STATUS_CMD, STOP_CMD, DO_SENSOR_READINGS_CMD, TIME_CMD, \
    FIRMWARE_VERSION_CMD, SERIAL_NUMBER_CMD, REQ_FILE_NAME_CMD, LOGGER_INFO_CMD, RUN_CMD, RWS_CMD, SD_FREE_SPACE_CMD, \
    SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, LOGGER_INFO_CMD_W, DIR_CMD, CALIBRATION_CMD, RESET_CMD, SENSOR_READINGS_CMD
from mat.logger_controller_ble_cc26x2 import LoggerControllerBLECC26X2
from mat.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.xmodem_ble import xmodem_get_file, XModemException
import pathlib
import subprocess as sp

# commands not present in USB loggers
BTC_CMD = 'BTC'
MOBILE_CMD = 'MBL'
HW_TEST_CMD = '#T1'
FORMAT_CMD = 'FRM'
CONFIG_CMD = 'CFG'
UP_TIME_CMD = 'UTM'
MY_TOOL_SET_CMD = 'MTS'
LOG_EN_CMD = 'LOG'
ERROR_WHEN_BOOT_OR_RUN_CMD = 'EBR'
CRC_CMD = 'CRC'
DWG_CMD = 'DWG'
_DEBUG_THIS_MODULE = 0


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
        if brand_microchip(mac):
            self.und = LoggerControllerBLERN4020(self)
        elif brand_ti(mac):
            self.und = LoggerControllerBLECC26X2(self)

        self.dlg = Delegate()

    def get_type(self):
        return self.und.type

    def open(self):
        retries = 3
        for i in range(retries):
            try:
                self.per = ble.Peripheral(self.address, iface=self.hci_if, timeout=10)
                # connection update request from cc26x2 takes 1000 ms
                time.sleep(1.1)
                self.per.setDelegate(self.dlg)
                self.svc = self.per.getServiceByUUID(self.und.UUID_S)
                self.cha = self.svc.getCharacteristics(self.und.UUID_C)[0]
                desc = self.cha.valHandle + 1
                self.per.writeCharacteristic(desc, b'\x01\x00')

                # don't remove, Linux hack or hangs at first BLE connection ever
                if is_connection_recent(self.address):
                    self.open_post()
                    return True
                self.per.disconnect()   # pragma: no cover
            except (AttributeError, ble.BTLEException):
                e = 'failed connection attempt {} of {}'
                print(e.format(i + 1, retries))
        return False

    def ble_write(self, data, response=False):  # pragma: no cover
        self.und.ble_write(data, response)

    def open_post(self):
        self.und.open_post()

    def close(self):
        try:
            self.per.disconnect()
            return True
        except AttributeError:
            return False

    def _cmd_ans_done(self, tag, debug=False):  # pragma: no cover
        """ ends last command sent's answer timeout """

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
        if a.startswith('ERR') or a.startswith('INV'):
            time.sleep(.5)
            return True

        # valid command, let's see
        return _ans(tag, a, b)

    def _cmd_ans_wait(self, tag: str):    # pragma: no cover
        """ starts answer timeout for last sent command """
        slow_ans = [RUN_CMD, RWS_CMD]
        w = 50 if tag in slow_ans else 5
        till = time.perf_counter() + w
        while 1:
            if time.perf_counter() > till:
                break
            if self._cmd_ans_done(tag, debug=False):
                break
            if self.per.waitForNotifications(0.001):
                till += 0.001
        # e.g. b'' / b'STS 00'
        return self.dlg.buf

    def _purge(self):   # pragma: no cover
        self.dlg.clr_buf()
        self.dlg.clr_x_buf()

    def _cmd(self, *args):   # pragma: no cover
        self._purge()
        self.dlg.set_file_mode(False)

        # discern command format
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

        # end building and send binary command
        to_send += chr(13)
        self.ble_write(to_send.encode())

        # wait answer w/ this tag string
        tag = cmd[:3]
        ans = self._cmd_ans_wait(tag).split()

        # e.g. [b'STS', b'020X']
        return ans

    def command(self, *args):    # pragma: no cover
        try:
            return self._cmd(*args)
        except ble.BTLEException as ex:
            # to be managed by app
            s = 'BLE: command() exception {}'.format(ex)
            raise ble.BTLEException(s)

    def flood(self, n):   # pragma: no cover
        """ attack check: sends command burst w/o caring answers """

        for i in range(n):
            cmd = STATUS_CMD
            cmd += chr(13)
            self.ble_write(cmd.encode())

    def _save_file(self, file, fol, s, sig=None):   # pragma: no cover
        """ called after _get_file(), downloads file w/ x-modem """

        self.dlg.set_file_mode(True)
        try:
            r, n = xmodem_get_file(self, sig, verbose=False)
        except XModemException:
            return False

        if not r:
            return False
        p = '{}/{}'.format(fol, file)
        with open(p, 'wb') as f:
            f.write(n)
            f.truncate(int(s))
        return True

    def get_file(self, file, fol, size, sig=None) -> bool:  # pragma: no cover
        # separates file downloads, allows logger x-modem to boot
        time.sleep(1)
        self.dlg.set_file_mode(False)

        # ensure fol string, not path_lib
        fol = str(fol)

        # send our own GET command
        dl = False
        try:
            cmd = 'GET {:02x}{}\r'.format(len(file), file)
            self.ble_write(cmd.encode())
            self.per.waitForNotifications(10)
            if self.dlg.buf and self.dlg.buf.endswith(b'GET 00'):
                dl = self._save_file(file, fol, size, sig)
            else:
                e = 'DBG: get_file() error, self.dlg.buf -> {}'
                print(e.format(self.dlg.buf))

        except ble.BTLEException as ex:
            s = 'BLE: GET() exception {}'.format(ex)
            raise ble.BTLEException(s)

        # clean-up, separate files download
        self.dlg.set_file_mode(False)
        time.sleep(1)
        return dl

    def get_time(self):
        ans = self.command(TIME_CMD)
        if not ans:
            return
        try:
            _time = ans[1].decode()[2:] + ' '
            _time += ans[2].decode()
            return datetime.strptime(_time, '%Y/%m/%d %H:%M:%S')
        except (ValueError, IndexError):
            print('GTM malformed: {}'.format(ans))
            return

    # wrapper for DIR command
    def _ls(self):
        rv = []
        c = 'DIR' if self.type == 'cc26x2' else 'DIR 00'

        for i in range(5):
            rv = self.command(c)
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
        if self.und.type == 'rn4020':
            s = 'BTC 00T,0006,0000,0064'
            _ = self.command(s)
            return _
        else:
            return 'wrong logger type'

    def _dwl_file(self, file, fol, s, sig=None):   # pragma: no cover
        """ called by dwg_file() """

        self.dlg.set_file_mode(True)
        file_built = bytes()

        # download chunk by chunk
        max_chunks = int(s / 2048)
        for c_n in range(max_chunks):
            _ = str(c_n)
            cmd = 'DWL {:02x}{}\r'.format(len(_), _)
            self.ble_write(cmd.encode())
            till = time.perf_counter() + 1
            while 1:
                self.dlg.x_buf = bytes()
                if self.per.waitForNotifications(.01):
                    file_built += self.dlg.x_buf
                    till = till + .01
                if time.perf_counter() > till:
                    break

        # write file to disk
        p = '{}/{}'.format(fol, file)
        with open(p, 'wb') as f:
            f.write(file_built)
            f.truncate(int(s))
        # todo --> add_crc check somewhre in MAT lib after downloads and gets
        return True

    def dwg_file(self, file, fol, size, sig=None) -> bool:  # pragma: no cover
        self.dlg.set_file_mode(False)

        # ensure fol string, not path_lib
        fol = str(fol)

        # send our own DWG command
        dl = False
        try:
            _ = '{} {:02x}{}\r'
            cmd = _.format(DWG_CMD, len(file), file)
            self.ble_write(cmd.encode())
            self.per.waitForNotifications(10)
            if self.dlg.buf and self.dlg.buf.endswith(b'DWG 00'):
                dl = self._dwl_file(file, fol, size, sig)
            else:
                e = 'DBG: dwg_file() error, self.dlg.buf -> {}'
                print(e.format(self.dlg.buf))

        except ble.BTLEException as ex:
            s = 'BLE: DWL() exception {}'.format(ex)
            raise ble.BTLEException(s)

        # clean-up, separate files download
        self.dlg.set_file_mode(False)
        time.sleep(1)
        return dl


# utilities
def _ls_wildcard(lis, ext, match=True):
    if lis is None:
        return {}

    if b'ERR' in lis:
        return b'ERR'

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
    return not brand_microchip(mac)


def brand_microchip(mac):
    mac = mac.lower()
    return mac.startswith('00:1e:c0:')


def ble_scan(hci_if, my_to=3.0):    # pragma: no cover
    # hci_if: hciX interface
    import sys
    try:
        s = ble.Scanner(iface=hci_if)
        return s.scan(timeout=my_to)
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


def _r_ble_linux_pars(banner, hci_if) -> (int, int, int):   # pragma: no cover
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


def w_ble_linux_pars(l1, l2, l3, hci_if):   # pragma: no cover
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
    known_li_types = [b'DO-1']
    for _ in known_li_types:
        if _ in bytes(rd):
            return True
    return False


def _ans(tag, a, b):
    # helper: function expects a 'TAG 00' answer when z is 0
    def _exp(z=0):
        _ = '{} 00'.format(tag) if z else tag
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
        DWG_CMD: lambda: _exp()
    }
    _el.setdefault(tag, lambda: _ans_unk(tag))
    rv = _el[tag]()

    # pause a bit, if so
    _allow_some_slow_down(rv, tag)
    return rv


def _allow_some_slow_down(rv, tag: str):
    _st = {
        LOGGER_INFO_CMD: .1,
        LOGGER_INFO_CMD_W: .1,
        CONFIG_CMD: .5,
        RUN_CMD: 1,
        STOP_CMD: 1,
        RWS_CMD: 1,
        SWS_CMD: 1
    }
    t = _st.get(tag, 0) if rv else 0
    time.sleep(t)


# helper: function returns false if tag is unknown
def _ans_unk(_tag):
    print('unknown tag {}'.format(_tag))
    return False
