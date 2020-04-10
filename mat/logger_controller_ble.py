import bluepy.btle as ble
import json
from datetime import datetime
import time
from mat.logger_controller import LoggerController, STATUS_CMD, STOP_CMD, DO_SENSOR_READINGS_CMD
from mat.logger_controller_ble_cc26x2 import LoggerControllerBLECC26X2
from mat.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.xmodem_ble import xmodem_get_file, XModemException


# commands not present in USB loggers
HW_TEST_CMD = '#T1'
FORMAT_CMD = 'FRM'
CONFIG_CMD = 'CFG'
UP_TIME_CMD = 'UTM'


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
        # todo: check bluepy new commits for BLE connection timeout
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
                self.open_post()
                return True
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

    def _done(self, tag):
        b = self.dlg.buf
        d = b.decode()
        if tag == 'GET' and d.startswith('GET 00'):
            # compound command GET: GET + n interactions XMD
            time.sleep(.5)
            return True
        elif tag == 'DIR' and b.endswith(b'\x04\n\r'):
            # compound command DIR: DIR + n answers
            return True
        if tag == STATUS_CMD and d.startswith(tag):
            return True if len(d) == 8 else False

    DEF_WAIT = .4
    ANS_WAIT = {
        # _done() overrides ANS_WAIT overrides DEF_WAIT
        'BTC': 3,
        STOP_CMD: 2,
        DO_SENSOR_READINGS_CMD: 3.2,
        HW_TEST_CMD: 10,
        CONFIG_CMD: 3,
        'GET': 3,
        'DIR': 3,
    }

    def _ans_wait(self, tag: str):    # pragma: no cover
        aw = self.ANS_WAIT
        dw = self.DEF_WAIT
        till = aw[tag] if tag in aw else dw
        till += time.time()
        while 1:
            if self.per.waitForNotifications(0.1):
                till += 0.1
            if time.time() > till:
                break
            if self._done(tag):
                break
        # e.g. b'STS 00'
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

        # answer as list of bytes() objects
        tag = cmd[:3]
        ans = self._ans_wait(tag).split()

        # e.g. [b'STS', b'0201']
        return ans

    def command(self, *args, retries=3):    # pragma: no cover
        for retry in range(retries):
            try:
                ans = self._cmd(*args)
                if ans:
                    return ans
                time.sleep(1)
            except ble.BTLEException as ex:
                # to be managed by app
                s = 'BLE: command() exception {}'.format(ex)
                raise ble.BTLEException(s)

    def _save_file(self, file, fol, s, sig=None):   # pragma: no cover
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
        ans = self.command('GET', file, retries=1)

        # ensure fol is string, not path_lib
        fol = str(fol)

        dl = False
        if ans == [b'GET', b'00']:
            dl = self._save_file(file, fol, size, sig)

        # do not remove, gives logger's XMODEM time to end
        self.dlg.set_file_mode(False)
        time.sleep(2)
        return dl

    def dwl_chunk(self, i, sig=None):
        self.dlg.clr_buf()

        # todo: do larger chunk number 2 bytes
        n = '{:02x}'.format(1)
        to_send = 'DWL {}{}\r'.format(n, i)
        self.ble_write(to_send.encode())

        timeout = time.perf_counter() + .1
        acc = bytes()
        while True:
            if time.perf_counter() > timeout:
                break
            self.per.waitForNotifications(.05)
            if len(self.dlg.buf):
                timeout = time.perf_counter() + .05
                print(self.dlg.buf, flush=True)
                acc += self.dlg.buf
                self.dlg.clr_buf()

        return acc

    def get_time(self):
        self.dlg.clr_buf()
        ans = self.command('GTM')
        if not ans:
            return
        try:
            _time = ans[1].decode()[2:] + ' '
            _time += ans[2].decode()
            return datetime.strptime(_time, '%Y/%m/%d %H:%M:%S')
        except (ValueError, IndexError):
            print('GTM malformed:'.format(ans))
            return

    # wrapper function for DIR command
    def _ls(self):
        self.dlg.clr_buf()
        # e.g. [b'.', b'..', b'a.lid', b'76', b'b.csv', b'10']
        rv = self.command('DIR 00', retries=1)
        return rv

    def ls_ext(self, ext):
        ans = self._ls()
        if ans in [[b'ERR'], [b'BSY'], None]:
            # e.g. logger not stopped
            return ans
        return _ls_keep_these(ans, ext)

    def ls_lid(self):
        return self.ls_ext(b'lid')

    def ls_not_lid(self):
        ans = self._ls()
        if ans in [[b'ERR'], [b'BSY'], None]:
            # e.g. logger not stopped
            return ans
        return _ls_keep_not_these(ans, b'lid')

    def send_cfg(self, cfg_json_dict: dict):  # pragma: no cover
        _as_string = json.dumps(cfg_json_dict)
        return self.command("CFG", _as_string, retries=1)


# utilities
def _ls_keep_these(lis, ext, match=True):
    files, idx = {}, 0
    while idx < len(lis):
        name = lis[idx]
        if name in [b'\x04']:
            break
        if name.endswith(ext) == match and name not in [b'.', b'..']:
            files[name.decode()] = int(lis[idx + 1])
        idx += 2
    return files


def _ls_keep_not_these(lis, ext):
    return _ls_keep_these(lis, ext, match=False)


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
