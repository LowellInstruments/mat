import bluepy.btle as btle
import time
import re
from mat.xmodem_ble import xmodem_get_file
from mat.logger_controller import LoggerController
from mat.logger_controller import DELAY_COMMANDS


class Delegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.buffer = bytes()
        self.read_buffer = []
        self.xmodem_mode = False
        self.x_buffer = bytes()

    # receive data from BLE logger
    def handleNotification(self, handler, data):
        if not self.xmodem_mode:
            # ascii mode
            self._handle_notifications_ascii_mode(data)
        else:
            # xmodem mode, just accumulate bytes
            self.x_buffer += data

    def _handle_notifications_ascii_mode(self, data):
        # required, some times changes its type
        if self.buffer == '':
            self.buffer = bytes()
        self.buffer += data
        self.buffer = self.buffer.replace(b'\n', b'')
        self._handle_notifications_ascii_mode_extract_buffer()

    def _handle_notifications_ascii_mode_extract_buffer(self):
        while b'\r' in self.buffer:
            # Make sure it doesn't start with CR
            if self.buffer.startswith(b'\r'):
                self.buffer = self.buffer[1:]
                continue
            pos = self.buffer.find(b'\r')
            in_str = self.buffer[:pos]
            self.buffer = self.buffer[pos + 1:]
            if in_str:
                # if complete string received, add to read_buffer
                self.read_buffer.append(in_str)

    @property
    def in_waiting(self):
        return True if self.xmodem_mode or self.read_buffer else False

    def read_line(self):
        # retrieve a line from a list of lines
        if not self.read_buffer:
            raise IndexError('Read buffer is empty')
        return self.read_buffer.pop(0)


class LoggerControllerBLE(LoggerController):
    def __init__(self, mac):
        super(LoggerController, self).__init__()
        self.peripheral_mac = mac
        self.peripheral = None
        self.delegate = None
        self.mldp_service = None
        self.mldp_data = None

    # called by __enter__ in class LoggerController
    def open(self):
        self.peripheral = btle.Peripheral()
        self.peripheral.connect(self.peripheral_mac)
        # one second required by RN4020
        time.sleep(1)
        self.delegate = Delegate()
        self.peripheral.setDelegate(self.delegate)
        UUID_SERV = '00035b03-58e6-07dd-021a-08123a000300'
        UUID_CHAR = '00035b03-58e6-07dd-021a-08123a000301'
        self.mldp_service = self.peripheral.getServiceByUUID(UUID_SERV)
        self.mldp_data = self.mldp_service.getCharacteristics(UUID_CHAR)[0]
        CCCD = self.mldp_data.valHandle + 1
        self.peripheral.writeCharacteristic(CCCD, b'\x01\x00')
        return True

    # called by __exit__ & __del__ (overriden here) in class LoggerController
    def close(self):
        try:
            print('Disconnecting...')
            self.peripheral.disconnect()
            time.sleep(1)
            return True
        except AttributeError:
            return False

    # def command(self, tag, data=None):
    #     # build command
    #     data = '' if data is None else data
    #     length = '{:02x}'.format(len(data))
    #     if tag == 'sleep' or tag == 'RFN':
    #         out_str = tag
    #     else:
    #         out_str = tag + ' ' + length + data
    #     self.write((out_str + chr(13)).encode())
    #
    #     # answer: RST, BSL and sleep don't return any
    #     if tag in ['RST', 'sleep', 'BSL']:
    #         return None
    #
    #     # answer: the ones that do
    #     return self._command_result(tag)

    def command(self, *args):
        # build command, same interface as other logger_controller_*
        tag = args[0]
        data = str(args[1]) if len(args) == 2 else ''
        length = '{:02x}'.format(len(data))
        if tag == 'sleep' or tag == 'RFN':
            out_str = tag
        else:
            out_str = tag + ' ' + length + data
        self.write((out_str + chr(13)).encode())

        # answer: RST, BSL and sleep don't return any
        if tag in ['RST', 'sleep', 'BSL']:
            return None

        # answer: the ones that do
        return self._command_result(tag)

    def _command_result(self, tag):
        while True:
            if not self.peripheral.waitForNotifications(3):
                raise LCBLEException('Logger timeout waiting: ' + tag)
            if self.delegate.in_waiting:
                return self._command_parse_back(tag)

    def _command_parse_back(self, tag):
        result = self.delegate.read_line()
        if result.startswith(tag.encode()):
            if tag in DELAY_COMMANDS:
                time.sleep(2)
            return result
        if result.startswith(b'ERR'):
            raise LCBLEException('MAT-1W returned ERR')
        if result.startswith(b'INV'):
            raise LCBLEException('MAT-1W reported invalid command')

    def control_command(self, data):
        # build and send control command
        self.delegate.buffer = ''
        self.delegate.read_buffer = []
        out_str = ('BTC 00' + data + chr(13)).encode()
        self.write(out_str)
        return self._control_command_result()

    def _control_command_result(self):
        last_rx = time.time()
        result = ''
        while not result.endswith('MLDP') and time.time() - last_rx < 3:
            result, last_rx = self._control_command_parse_back(result, last_rx)
        return result

    def _control_command_parse_back(self, result, last_rx):
        if self.peripheral.waitForNotifications(0.05):
            last_rx = time.time()
        if self.delegate.in_waiting:
            result += self.delegate.read_line().decode()
        return result, last_rx

    # write to logger BLE characteristic
    def write(self, data, response=False):
        data2 = [data[i:i + 1] for i in range(len(data))]
        for c in data2:
            self.mldp_data.write(c, withResponse=response)

    # def list_files(self):
    #     # build DIR command
    #     files = []
    #     self.delegate.buffer = ''
    #     self.delegate.read_buffer = []
    #     self.write(('DIR 00' + chr(13)).encode())
    #
    #     # wait for DIR command answer
    #     last_rx = time.time()
    #     while True:
    #         self.peripheral.waitForNotifications(0.01)
    #         # check if there is a whole line in the buffer
    #         if self.delegate.in_waiting:
    #             last_rx = time.time()
    #             file_str = self.delegate.read_line()
    #             # EOT received so end of file list
    #             if file_str == b'\x04':
    #                 break
    #             file_str = file_str.decode()
    #             re_obj = re.search(r'([\x20-\x7E]+)\t+(\d*)', file_str)
    #             try:
    #                 file_name = re_obj.group(1)
    #                 file_size = int(re_obj.group(2))
    #             except (AttributeError, IndexError):
    #                 raise LCBLEException(
    #                     'DIR bad file_str {}.'.format(file_str))
    #             files.append((file_name, file_size))
    #         # there was a timeout during DIR answer
    #         if time.time() - last_rx > 3:
    #             raise LCBLEException('Timeout while getting file list.')
    #     return files

    # know which files are in remote logger
    def dir_command(self):
        self.delegate.buffer = ''
        self.delegate.read_buffer = []
        self.write(('DIR 00' + chr(13)).encode())
        return self._dir_command_result()

    # grab dir_command() answer
    def _dir_command_result(self):
        # todo: address corresponding test
        files = []
        answer_bytes = bytes()
        last_rx = time.time()
        while answer_bytes != b'\x04':
            # receive via BLE, parse any waiting line in buffer
            self.peripheral.waitForNotifications(0.01)
            if self.delegate.in_waiting:
                last_rx = time.time()
                answer_bytes = self._dir_command_parse_back(files)
            # timeout while DIR answer, quit
            if time.time() - last_rx > 3:
                raise LCBLEException('Timeout while getting file list.')
        return files

    def _dir_command_parse_back(self, files):
        answer_bytes = self.delegate.read_line()
        file_str = answer_bytes.decode()
        re_obj = re.search(r'([\x20-\x7E]+)\t+(\d*)', file_str)
        try:
            file_name = re_obj.group(1)
            file_size = int(re_obj.group(2))
            files.append((file_name, file_size))
        except (AttributeError, IndexError):
            pass
        finally:
            return answer_bytes

    # obtain a file from the logger via BLE
    def get_file(self, filename, dfolder):  # pragma: no cover
        # required vars and switch to xmodem mode
        self.delegate.buffer = ''
        self.delegate.x_buffer = bytes()
        self.command('GET', filename)
        self.delegate.xmodem_mode = True

        # try to receive via xmodem with our logger_controller
        result, bytes_received = xmodem_get_file(self)
        if result:
            full_file_path = dfolder + '/' + filename
            with open(full_file_path, 'wb') as f:
                f.write(bytes_received)
        else:
            print('xmodem_get_files() returned {}'.format(bytes_received))
        self.delegate.xmodem_mode = False

    # prevent garbage collector
    def __del__(self):
        pass


class LCBLEException(Exception):
    pass
