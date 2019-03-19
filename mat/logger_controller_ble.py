import bluepy.btle as btle
import time
import datetime
from mat.logger_controller import LoggerController
from mat.xmodem_ble import xmodem_get_file, XModemException


class MyDelegate(btle.DefaultDelegate):
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

    def set_file_mode(self):
        self.file_mode = True

    def clear_file_mode(self):
        self.file_mode = False


class LoggerControllerBLE(LoggerController):
    def __init__(self, mac):
        super(LoggerController, self).__init__()
        self.peripheral_mac = mac
        self.peripheral = None
        self.delegate = None
        self.service = None
        self.characteristic = None

    def open(self):
        try:
            self.peripheral = btle.Peripheral()
            self.delegate = MyDelegate()
            self.peripheral.setDelegate(self.delegate)
            self.peripheral.connect(self.peripheral_mac)
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

    def ble_write(self, data, response=False):
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
        self.delegate.clear_file_mode()

        # prepare transmission vars
        cmd = str(args[0])
        cmd_data = str(args[1]) if len(args) == 2 else ''
        cmd_data_len = '{:02x}'.format(len(cmd_data)) if cmd_data else ''
        cmd_to_send = cmd + ' ' + cmd_data_len + cmd_data

        # format command as binary
        if cmd in ('sleep', 'RFN'):
            cmd_to_send = cmd
        cmd_to_send += chr(13)
        cmd_to_send = cmd_to_send.encode()

        # send command as binary
        # print('Command being sent = {}'.format(cmd_to_send))
        self.ble_write(cmd_to_send)

        # check if this command will wait for an answer
        if cmd in ('RST', 'sleep', 'BSL'):
            return None

        # answer is a list of b'xxx'
        cmd_answer = self._command_answer(cmd).split()
        return cmd_answer

    def _command_answer(self, cmd):
        cmd_timeouts = {'BTC': 3, 'GET': 3}
        end_time = cmd_timeouts[cmd[:3]] if cmd[:3] in cmd_timeouts else 1
        timeout = time.time() + end_time
        while time.time() < timeout:
            self.peripheral.waitForNotifications(0.1)
        return self.delegate.buffer

    # obtain a file from the logger via BLE using xmodem
    def get_file(self, filename, folder, size):  # pragma: no cover
        self.delegate.clear_delegate_buffer()
        self.delegate.clear_delegate_x_buffer()

        self.delegate.clear_file_mode()
        answer_get = self.command('GET', filename)

        try:
            file_dl = self._save_file(answer_get, filename, folder, size)
        except XModemException as xme:
            print('XModemException caught at lc_ble --> {}'.format(xme))
            file_dl = False
        finally:
            self.delegate.clear_file_mode()

        return file_dl

    def _save_file(self, answer_get, filename, folder, size):
        if answer_get[0] == b'GET':
            self.delegate.set_file_mode()
            result, bytes_received = xmodem_get_file(self)
            if result:
                full_file_path = folder + '/' + filename
                with open(full_file_path, 'wb') as f:
                    f.write(bytes_received)
                    f.truncate(int(size))
            return True
        print('File NOT downloaded.')
        return False

    def list_files(self):
        self.delegate.clear_delegate_buffer()
        answer_dir = self.command('DIR 00')
        if answer_dir:
            files = answer_dir[0:][::2]
            sizes = answer_dir[1:][::2]
            return dict(zip(files, sizes))
        return dict()

    def get_time(self):
        self.delegate.clear_delegate_buffer()
        answer_gtm = self.command('GTM')
        if answer_gtm:
            logger_time = answer_gtm[1].decode()
            logger_time = logger_time[2:] + ' ' + answer_gtm[2].decode()
            time_format = '%Y/%m/%d %H:%M:%S'
            return datetime.datetime.strptime(logger_time, time_format)
