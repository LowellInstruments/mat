import bluepy.btle as btle
import time
import datetime
from mat.logger_controller import LoggerController
from mat.xmodem_ble import xmodem_get_file, XModemException


class Delegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
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

    WAIT_TIME = {'BTC': 3, 'GET': 3}

    def __init__(self, mac):
        super().__init__(mac)
        self.peripheral = None
        self.delegate = None
        self.service = None
        self.characteristic = None

    def open(self):
        try:
            self.peripheral = btle.Peripheral()
            self.delegate = Delegate()
            self.peripheral.setDelegate(self.delegate)
            self.peripheral.connect(self.address)
            # one second required by RN4020
            time.sleep(1)
            uuid_service = '00035b03-58e6-07dd-021a-08123a000300'
            uuid_char = '00035b03-58e6-07dd-021a-08123a000301'
            self.service = self.peripheral.getServiceByUUID(uuid_service)
            self.characteristic = self.service.getCharacteristics(uuid_char)[0]
            descriptor = self.characteristic.valHandle + 1
            self.peripheral.writeCharacteristic(descriptor, b'\x01\x00')
            return True
        except AttributeError:
            return False

    def close(self):
        try:
            self.peripheral.disconnect()
            return True
        except AttributeError:
            return False

    def ble_write(self, data, response=False):  # pragma: no cover
        binary_data = [data[i:i + 1] for i in range(len(data))]
        for each in binary_data:
            self.characteristic.write(each, withResponse=response)

    def command(self, *args):
        for retries in range(3):
            try:
                result = self._command(*args)
                if result:
                    return result
            except btle.BTLEException:
                time.sleep(1)

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

    def _wait_for_command_answer(self, cmd):
        end_time = self.WAIT_TIME[cmd[:3]] if cmd[:3] in self.WAIT_TIME else 1
        wait_time = time.time() + end_time
        while time.time() < wait_time:
            self.peripheral.waitForNotifications(0.1)
        return self.delegate.buffer

    def get_time(self):
        self.delegate.clear_delegate_buffer()
        answer_gtm = self.command('GTM')
        if answer_gtm:
            logger_time = answer_gtm[1].decode()
            logger_time = logger_time[2:] + ' ' + answer_gtm[2].decode()
            time_format = '%Y/%m/%d %H:%M:%S'
            return datetime.datetime.strptime(logger_time, time_format)

    def list_files(self):
        self.delegate.clear_delegate_buffer()
        answer_dir = self.command('DIR 00')
        # example answer_dir
        # [b'a.lid', b'1234', b'd.lid', b'10000', b'MAT.cfg', b'216', b'\x04']
        if answer_dir:
            files = answer_dir[0::2]
            sizes = answer_dir[1::2]
            return dict(zip(files, sizes))
        return dict()

    def get_file(self, filename, folder, size):  # pragma: no cover
        self.delegate.clear_delegate_buffer()
        self.delegate.clear_delegate_x_buffer()

        self.delegate.set_file_mode(False)
        answer_get = self.command('GET', filename)

        try:
            file_dl = self._save_file(answer_get, filename, folder, size)
        except XModemException as xme:
            print('XModemException caught at lc_ble --> {}'.format(xme))
            file_dl = False
        finally:
            self.delegate.set_file_mode(False)

        return file_dl

    def _save_file(self, answer_get, filename, folder, s):   # pragma: no cover
        if answer_get[0] == b'GET':
            self.delegate.set_file_mode(True)
            result, bytes_received = xmodem_get_file(self)
            if result:
                full_file_path = folder + '/' + filename
                with open(full_file_path, 'wb') as f:
                    f.write(bytes_received)
                    f.truncate(int(s))
            return True
        return False
