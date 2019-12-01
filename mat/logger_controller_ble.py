import bluepy.btle as bluepy
import json
import datetime
import time
from mat.logger_controller import LoggerController
from mat.logger_controller_ble_cc26x2 import LoggerControllerBLECC26X2
from mat.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.xmodem_ble import xmodem_get_file, XModemException


class Delegate(bluepy.DefaultDelegate):
    def __init__(self):
        bluepy.DefaultDelegate.__init__(self)
        self.buffer = bytes()
        self.x_buffer = bytes()
        self.file_mode = False

    def handleNotification(self, c_handle, data):
        if not self.file_mode:
            self.buffer += data
        else:
            self.x_buffer += data

    def clear_delegate_buffer(self):
        self.buffer = bytes()

    def clear_delegate_x_buffer(self):
        self.x_buffer = bytes()

    def set_file_mode(self, state):
        self.file_mode = state


class LoggerControllerBLE(LoggerController):

    WAIT_TIME = {'BTC': 3, 'GET': 3, 'RWS': 2}

    @staticmethod
    def is_manufacturer_ti(mac):
        mac = mac.lower()
        return mac.startswith('80:6f:b0:') or mac.startswith('04:ee:03:')

    @staticmethod
    def is_manufacturer_microchip(mac):
        mac = mac.lower()
        return mac.startswith('00:1e:c0:')

    def __init__(self, mac):
        super().__init__(mac)
        # set underlying (u) python BLE module being used
        if self.is_manufacturer_ti(mac):
            self.u = LoggerControllerBLECC26X2(mac)
        elif self.is_manufacturer_microchip(mac):
            self.u = LoggerControllerBLERN4020(mac)
        self.delegate = Delegate()

    def open(self):
        for counter in range(3):
            try:
                self.u.peripheral = bluepy.Peripheral(self.u.address)
                # connection update request from cc26x2 takes 1000 ms
                time.sleep(1.1)
                self.u.peripheral.setDelegate(self.delegate)
                self.u.svc = self.u.peripheral.getServiceByUUID(self.u.UUID_S)
                self.u.cha = self.u.svc.getCharacteristics(self.u.UUID_C)[0]
                descriptor = self.u.cha.valHandle + 1
                self.u.peripheral.writeCharacteristic(descriptor, b'\x01\x00')
                self.open_after()
                return True
            except (AttributeError, bluepy.BTLEException):
                pass
        return False

    def ble_write(self, data, response=False):  # pragma: no cover
        self.u.ble_write(data, response)

    def open_after(self):
        self.u.open_after()

    def close(self):
        try:
            self.u.peripheral.disconnect()
            return True
        except AttributeError:
            return False

    def command(self, *args, retries=3):    # pragma: no cover
        for retry in range(retries):
            try:
                result = self._command(*args)
                if result:
                    return result
            except bluepy.BTLEException:
                # to be managed by app
                s = 'BLE command() exception'
                print(s)
                raise bluepy.BTLEException(s)
        return b'BSY'

    def _command(self, *args):
        # prepare reception vars
        self.delegate.clear_delegate_buffer()
        self.delegate.set_file_mode(False)

        # prepare transmission vars
        cmd = str(args[0])
        cmd_data = str(args[1]) if len(args) == 2 else ''
        cmd_data_len = '{:02x}'.format(len(cmd_data)) if cmd_data else ''
        cmd_to_send = cmd + ' ' + cmd_data_len + cmd_data

        # format and send binary command
        if cmd in ('sleep', 'RFN'):
            cmd_to_send = cmd
        cmd_to_send += chr(13)
        cmd_to_send = cmd_to_send.encode()
        self.ble_write(cmd_to_send)

        # check if this command will wait for an answer
        if cmd in ('RST', 'sleep', 'BSL'):
            return None

        # collect and return answer as list of bytes() objects
        cmd_answer = self._wait_for_command_answer(cmd).split()
        return cmd_answer

    def _shortcut_command_answer(self, cmd):
        if cmd == 'GET' and self.delegate.buffer == b'GET 00':
            return True
        if cmd == 'DIR' and self.delegate.buffer.endswith(b'\x04\n\r'):
            return True

    def _wait_for_command_answer(self, cmd):    # pragma: no cover
        tag = cmd[:3]
        end_time = self.WAIT_TIME[tag] if tag in self.WAIT_TIME else 1
        wait_time = time.time() + end_time
        while time.time() < wait_time:
            if self.u.peripheral.waitForNotifications(0.1):
                wait_time += 0.1
            if self._shortcut_command_answer(tag):
                break
        return self.delegate.buffer

    def get_time(self):
        self.delegate.clear_delegate_buffer()
        answer_gtm = self.command('GTM')
        if not answer_gtm:
            return False
        logger_time = answer_gtm[1].decode()[2:] + ' '
        logger_time += answer_gtm[2].decode()
        time_format = '%Y/%m/%d %H:%M:%S'
        try:
            # we may receive a truncated answer (e.g. '2019/08/12 12')
            return datetime.datetime.strptime(logger_time, time_format)
        except ValueError:
            return False

    def get_file(self, filename, folder, size):  # pragma: no cover
        self.delegate.clear_delegate_buffer()
        self.delegate.clear_delegate_x_buffer()

        self.delegate.set_file_mode(False)
        answer_get = self.command('GET', filename)

        try:
            file_dl = self._save_file(answer_get, filename, folder, size)
        except XModemException:
            file_dl = False
        finally:
            self.delegate.set_file_mode(False)

        # do not remove, gives logger's XMODEM time to end
        time.sleep(2)
        return file_dl

    def _save_file(self, answer_get, filename, folder, s):   # pragma: no cover
        if answer_get is not None and answer_get[0] == b'GET':
            self.delegate.set_file_mode(True)
            result, bytes_received = xmodem_get_file(self)
            if result:
                full_file_path = folder + '/' + filename
                with open(full_file_path, 'wb') as f:
                    f.write(bytes_received)
                    f.truncate(int(s))
            return True
        return False

    # wrapper function for DIR command to list lid files
    def ls_lid(self):
        self.delegate.clear_delegate_buffer()
        ans = self.command('DIR 00', retries=1)
        files = dict()
        index = 0
        while index < len(ans):
            name = ans[index]
            if name == b'\x04' or name == b'BSY':
                break
            if name.endswith(b'lid'):
                files[name.decode()] = int(ans[index + 1])
                index += 1
            index += 1
        return files

    def ls_not_lid(self):
        self.delegate.clear_delegate_buffer()
        ans = self.command('DIR 00', retries=1)
        files = dict()
        index = 0
        while index < len(ans):
            name = ans[index]
            if name == b'\x04' or name == b'BSY':
                break
            if name.endswith(b'lid'):
                index += 2
                continue
            if not name.endswith(b'lid'):
                files[name.decode()] = int(ans[index + 1])
                index += 2
        return files

    def send_cfg(self, cfg_file_as_json_dict):  # pragma: no cover
        cfg_file_as_string = json.dumps(cfg_file_as_json_dict)
        return self.command("CFG", cfg_file_as_string, retries=1)

    def _ensure_cmd(self, c, s=''):
        self.delegate.clear_delegate_buffer()
        a = self.command(c, s)
        if a in ['BSY', None]:
            return False
        return a

    def ensure_stop(self):
        rv = self._ensure_cmd('STP')
        if rv:
            return rv
        self.u.peripheral.disconnect()
        return False

    def ensure_sws(self, s=''):
        rv = self._ensure_cmd('SWS', s)
        if rv:
            return rv
        self.u.peripheral.disconnect()
        return False
