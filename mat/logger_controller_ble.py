import bluepy.btle as ble
import json
from datetime import datetime
import time
import math
from mat.logger_controller import LoggerController, STATUS_CMD, STOP_CMD, DO_SENSOR_READINGS_CMD, TIME_CMD, \
    FIRMWARE_VERSION_CMD, SERIAL_NUMBER_CMD, REQ_FILE_NAME_CMD, LOGGER_INFO_CMD, RUN_CMD, RWS_CMD, SD_FREE_SPACE_CMD, \
    SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD
from mat.logger_controller_ble_cc26x2 import LoggerControllerBLECC26X2
from mat.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.xmodem_ble import xmodem_get_file, XModemException
import pathlib


# commands not present in USB loggers
HW_TEST_CMD = '#T1'
FORMAT_CMD = 'FRM'
CONFIG_CMD = 'CFG'
UP_TIME_CMD = 'UTM'
MY_TOOL_SET_CMD = 'MTS'
LOG_EN_CMD = 'LOG'


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
        super().__init__(mac)
        self.address = mac
        self.hci_if = hci_if
        self.per = None
        self.svc = None
        self.cha = None
        # set underlying BLE class
        if brand_ti(mac):
            self.und = LoggerControllerBLECC26X2(self)
        elif brand_microchip(mac):
            self.und = LoggerControllerBLERN4020(self)
        else:
            raise ble.BTLEException('unknown brand')
        self.dlg = Delegate()

    def open(self):
        for counter in range(3):
            try:
                self.per = ble.Peripheral(self.address, iface=self.hci_if)
                # connection update request from cc26x2 takes 1000 ms
                time.sleep(1.1)
                self.per.setDelegate(self.dlg)
                self.svc = self.per.getServiceByUUID(self.und.UUID_S)
                self.cha = self.svc.getCharacteristics(self.und.UUID_C)[0]
                desc = self.cha.valHandle + 1
                self.per.writeCharacteristic(desc, b'\x01\x00')

                # hack for linux, or hangs at first BLE connection
                r = is_connection_recent(self.address)
                if r:
                    self.open_post()
                    return True
                self.per.disconnect()
                time.sleep(1)
            except (AttributeError, ble.BTLEException):
                pass
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

    def __cmd_ans_done(self, tag):
        """ interrupts answer timeout for last sent command """

        rv = None
        b = self.dlg.buf

        try:
            # normal ASCII commands
            d = b.decode()
        except UnicodeError:
            # DWL ASCII command, not binary as XMD
            tag = 'DWL'
            d = b

        if tag == 'DWL':
            return True
        elif tag == 'GET' and d.startswith('GET 00'):
            # do not remove, gives logger time to open file
            time.sleep(.5)
            rv = True
        elif tag == 'DIR' and b.endswith(b'\x04\n\r'):
            rv = True
        elif tag == STATUS_CMD and d.startswith(tag):
            rv = True if len(d) == 8 else False
        elif tag == LOG_EN_CMD and d.startswith(tag):
            rv = True if len(d) == 8 else False
        elif tag == FIRMWARE_VERSION_CMD and d.startswith(tag):
            rv = True if len(d) == 6 + 6 else False
        elif tag == SERIAL_NUMBER_CMD and d.startswith(tag):
            rv = True if len(d) == 6 + 7 else False
        elif tag == UP_TIME_CMD and d.startswith(tag):
            rv = True
        elif tag == TIME_CMD and d.startswith(tag):
            rv = True if len(d) == 6 + 19 else False
        elif tag == SET_TIME_CMD:
            rv = d.startswith('STM 00')
        elif tag == REQ_FILE_NAME_CMD:
            rv = d.startswith('RFN 00') or d.endswith('.lid')
        elif tag == LOGGER_INFO_CMD and d.startswith(tag):
            rv = (len(d) <= 6 + 7)
        elif tag == SD_FREE_SPACE_CMD and d.startswith(tag):
            rv = (len(d) == 6 + 8)
        elif tag == CONFIG_CMD and d.startswith(tag):
            rv = d.startswith('CFG 00')
            time.sleep(.5)
        elif tag == DEL_FILE_CMD and d.startswith(tag):
            rv = d.startswith('DEL 00')
        elif tag in [RUN_CMD, STOP_CMD, RWS_CMD, SWS_CMD]:
            rv = d.startswith('{} 00'.format(tag))
            time.sleep(1)
        elif tag == MY_TOOL_SET_CMD:
            rv = d.startswith('{} 00'.format(tag))
        elif tag == DO_SENSOR_READINGS_CMD:
            rv = d.startswith('{} '.format(tag))
            rv = rv and (len(d) <= 6 + 12)
        elif tag == 'DWG' and d.startswith('DWG'):
            rv = True
        # todo: add any missing fast quit waiting rules
        elif d.startswith('ERR') or d.startswith('INV'):
            time.sleep(.5)
            rv = True
        else:
            # here while answer being collected
            pass
        return rv

    def __cmd_ans_wait(self, tag: str):    # pragma: no cover
        """ starts answer timeout for last sent command """

        w = 50 if tag in [RUN_CMD, RWS_CMD] else 5
        till = time.perf_counter() + w
        while 1:
            if self.per.waitForNotifications(0.1):
                till += 0.1
            if time.perf_counter() > till:
                break
            if self.__cmd_ans_done(tag):
                break
        # e.g. b'STS 00' / b''
        return self.dlg.buf

    def _cmd(self, *args):
        # reception vars
        self.dlg.clr_buf()
        self.dlg.set_file_mode(False)

        # transmission vars
        cmd = str(args[0])
        arg = str(args[1]) if len(args) == 2 else ''
        n = '{:02x}'.format(len(arg)) if arg else ''
        to_send = cmd + ' ' + n + arg

        # send binary command
        if cmd in ('sleep', 'RFN'):
            to_send = cmd
        to_send += chr(13)
        self.ble_write(to_send.encode())

        # wait for an answer w/ this tag string
        tag = cmd[:3]
        ans = self.__cmd_ans_wait(tag).split()

        # e.g. [b'STS', b'0201']
        return ans

    def command(self, *args):    # pragma: no cover
        try:
            return self._cmd(*args)
        except ble.BTLEException as ex:
            # to be managed by app
            s = 'BLE: command() exception {}'.format(ex)
            raise ble.BTLEException(s)

    def flood(self, n):
        """ robust check: sends command burst w/o caring answers """

        for i in range(n):
            cmd = STATUS_CMD
            cmd += chr(13)
            self.ble_write(cmd.encode())

    def _save_file(self, file, fol, s, sig=None):   # pragma: no cover
        """ called after _get_file(), downloads file w/ x-modem """

        try:
            self.dlg.set_file_mode(True)
            r, bytes_rx = xmodem_get_file(self, sig)
            if r:
                p = '{}/{}'.format(fol, file)
                with open(p, 'wb') as f:
                    f.write(bytes_rx)
                    f.truncate(int(s))
            return True
        except XModemException:
            return False

    def get_file(self, file, fol, size, sig=None):  # pragma: no cover
        self.dlg.clr_buf()
        self.dlg.clr_x_buf()
        self.dlg.set_file_mode(False)

        # send GET command
        ans = self.command('GET', file)

        # ensure fol is string, not path_lib
        fol = str(fol)

        # did GET command went OK
        dl = False
        if ans == [b'GET', b'00']:
            dl = self._save_file(file, fol, size, sig)

        # do not remove, gives peer's x-modem time to end
        time.sleep(2)
        self.dlg.set_file_mode(False)
        self.dlg.clr_buf()
        self.dlg.clr_x_buf()
        return dl

    def dwg_file(self, file, fol, s, sig=None):  # pragma: no cover
        self.dlg.clr_buf()

        # send DWG command
        ans = self.command('DWG', file)
        if ans != [b'DWG', b'00']:
            return False

        # download file
        acc = bytes()
        n = math.ceil(s / 2048)
        for i in range(n):
            acc += self._dwl_chunk(i, sig)

        # write file, ensure fol not path_lib
        fol = str(fol)
        p = '{}/{}'.format(fol, file)
        with open(p, 'wb') as f:
            f.write(acc)
            f.truncate(int(s))

        # separate batch file downloads
        time.sleep(1)
        print('DWL {} of {} bytes'.format(acc, s))
        return len(acc) == s

    def _dwl_chunk(self, i, sig=None):
        self.dlg.clr_buf()
        i = str(i)
        to_send = 'DWL {:02x}{}\r'.format(len(i), i)
        self.ble_write(to_send.encode())

        t_o = time.perf_counter() + .1
        acc = bytes()
        while True:
            if time.perf_counter() > t_o:
                break
            if len(acc) >= 2048:
                break
            if self.per.waitForNotifications(.5):
                t_o = time.perf_counter() + .5
                # skip chunk length byte
                n = int(self.dlg.buf[0])
                c = self.dlg.buf[1:]
                acc += c
                sig.emit(n)
                self.dlg.clr_buf()

        time.sleep(.1)
        return acc

    def get_time(self):
        self.dlg.clr_buf()
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

    # wrapper function for DIR command
    def _ls(self):
        self.dlg.clr_buf()
        rv = self.command('DIR 00')
        # e.g. [b'.', b'0', b'..', b'0', b'dummy.lid', b'4096', b'\x04']
        return rv

    def ls_ext(self, ext):
        return _ls_wildcard(self._ls(), ext, match=True)

    def ls_lid(self):
        ext = b'lid'
        return self.ls_ext(ext)

    def ls_not_lid(self):
        ext = b'lid'
        return _ls_wildcard(self._ls(), ext, match=False)

    def send_cfg(self, cfg_json_dict: dict):  # pragma: no cover
        _as_string = json.dumps(cfg_json_dict)
        return self.command(CONFIG_CMD, _as_string)


# utilities
def _ls_wildcard(lis, ext, match=True):
    files, idx = {}, 0
    while idx < len(lis):
        name = lis[idx]
        if name in [b'\x04', b'ERR']:
            break
        if name.endswith(ext) == match and name not in [b'.', b'..']:
            files[name.decode()] = int(lis[idx + 1])
        idx += 2
    return files


def brand_ti(mac):
    mac = mac.lower()
    return mac.startswith('80:6f:b0:') or mac.startswith('04:ee:03:')


def brand_microchip(mac):
    mac = mac.lower()
    return mac.startswith('00:1e:c0:')


def ble_scan(hci_if, my_to=3.0):
    # hci_if: hciX interface
    import sys
    try:
        s = ble.Scanner(iface=hci_if)
        return s.scan(timeout=my_to)
    except OverflowError:
        e = 'SYS: overflow on BLE scan, maybe date time error'
        print(e)
        sys.exit(1)


def is_connection_recent(mac):
    mac = str(mac).replace(':', '')
    path = pathlib.Path('/dev/shm/{}'.format(mac))
    if path.exists():
        print('mac found cached')
        return True
    print('mac not cached, caching it...')
    path.touch()
    return False
