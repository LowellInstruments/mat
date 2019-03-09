import bluepy.btle as btle
import time
import re
import crc16
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
            # required, some times changes its type
            if self.buffer == '':
                self.buffer = bytes()
            self.buffer += data
            self.buffer = self.buffer.replace(b'\n', b'')
            while b'\r' in self.buffer:
                # Make sure it doesn't start with CR
                if self.buffer.startswith(b'\r'):
                    self.buffer = self.buffer[1:]
                    continue
                pos = self.buffer.find(b'\r')
                in_str = self.buffer[:pos]
                self.buffer = self.buffer[pos+1:]
                if in_str:
                    # if complete string received, add to read_buffer
                    self.read_buffer.append(in_str)
        else:
            # xmodem mode, just accumulate bytes
            self.x_buffer += data

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

    def close(self):
        try:
            print('Disconnecting...')
            self.peripheral.disconnect()
            time.sleep(1)
            return True
        except AttributeError:
            return False

    # send commands to MSP430 such as RUN or STP
    def command(self, tag, data=None):
        return_val = None
        data = '' if data is None else data
        length = '%02x' % len(data)

        # build command
        if tag == 'sleep' or tag == 'RFN':
            out_str = tag
        else:
            out_str = tag + ' ' + length + data

        # send command via BLE
        self.write((out_str + chr(13)).encode())

        # RST, BSL and sleep don't return tags
        if tag == 'RST' or tag == 'sleep' or tag == 'BSL':
            tag_waiting = ''
        else:
            tag_waiting = tag

        # wait command answer
        while tag_waiting:
            if not self.peripheral.waitForNotifications(3):
                raise LCBLEException('Logger timeout waiting: ' + tag_waiting)

            if self.delegate.in_waiting:
                inline = self.delegate.read_line()
                if inline.startswith(tag_waiting.encode()):
                    return_val = inline
                    break
                elif inline.startswith(b'ERR'):
                    raise LCBLEException('MAT-1W returned ERR')
                elif inline.startswith(b'INV'):
                    raise LCBLEException('MAT-1W reported invalid command')
        return return_val

    # send command to MSP430 so it configures RN4020 with it
    def control_command(self, data):
        # vars
        self.delegate.buffer = ''
        self.delegate.read_buffer = []

        # build and send control command
        out_str = ('BTC 00' + data + chr(13)).encode()
        self.write(out_str)

        # wait for answer to control command
        last_rx = time.time()
        return_val = ''
        while time.time() - last_rx < 3:
            # can return: '', 'CMDAOKMDLP', 'PERRAOKMDLP'
            if self.peripheral.waitForNotifications(0.05):
                last_rx = time.time()
            if self.delegate.in_waiting:
                inline = self.delegate.read_line()
                return_val += inline.decode()
                if return_val.endswith('MLDP'):
                    break
        if return_val == '':
            return_val = 'DIDNOT'
        return return_val

    # write to logger BLE characteristic
    def write(self, data, response=False):
        data2 = [data[i:i + 1] for i in range(len(data))]
        for c in data2:
            self.mldp_data.write(c, withResponse=response)

    # know which files are in remote logger
    def list_files(self):
        # build DIR command
        files = []
        self.delegate.buffer = ''
        self.delegate.read_buffer = []
        self.write(('DIR 00' + chr(13)).encode())

        # wait for DIR command answer
        last_rx = time.time()
        while True:
            self.peripheral.waitForNotifications(0.01)
            # check if there is a whole line in the buffer
            if self.delegate.in_waiting:
                last_rx = time.time()
                file_str = self.delegate.read_line()
                # EOT received so end of file list
                if file_str == b'\x04':
                    break
                file_str = file_str.decode()
                re_obj = re.search(r'([\x20-\x7E]+)\t+(\d*)', file_str)
                try:
                    file_name = re_obj.group(1)
                    file_size = int(re_obj.group(2))
                except (AttributeError, IndexError):
                    raise LCBLEException('DIR bad file_str {}.'.format(file_str))
                files.append((file_name, file_size))
            # there was a timeout during DIR answer
            if time.time() - last_rx > 3:
                raise LCBLEException('Timeout while getting file list.')
        return files

    # obtain a file from the logger via BLE
    def get_file(self, filename, dfolder):  # pragma: no cover
        # required vars and switch to xmodem mode
        self.delegate.buffer = ''
        self.delegate.x_buffer = bytes()
        self.command('GET', filename)
        self.delegate.xmodem_mode = True

        # variables
        MAXRETRANS = 25
        retrans = MAXRETRANS
        SOH = b'\x01'
        STX = b'\x02'
        EOT = b'\x04'
        ACK = b'\x06'
        CAN = b'\x18'
        bufsz = 0
        whole_file = bytes()
        trychar = b'C'

        # start xmodem protocol
        while True:
            # tries for CONTROL characters
            something_to_rx = False
            for retry in range(16):
                # send C, which can fail, too
                if trychar:
                    self.delegate.x_buffer = bytes()
                    whole_file = bytes()
                    self.write(trychar)
                # collect control bytes back
                self._collect(1)
                c = self._inbyte(0)
                # 128 bytes page incoming
                if c == SOH:
                    bufsz = 128
                    something_to_rx = True
                    break
                # 1k size page incoming
                elif c == STX:
                    bufsz = 1024
                    something_to_rx = True
                    break
                # end of transmission
                elif c == EOT:
                    print('eot')
                    self.delegate.x_buffer = bytes()
                    self.write(ACK)
                    full_file_path = dfolder + '/' + filename
                    with open(full_file_path, 'wb') as f:
                        f.write(whole_file)
                    self.delegate.xmodem_mode = False
                    return len(whole_file)
                # remote side cancelled transmission
                elif c == CAN:
                    self._collect(1)
                    c = self._inbyte(0)
                    if c == CAN:
                        self.delegate.x_buffer = bytes()
                        self.write(ACK)
                        self.delegate.xmodem_mode = False
                        return -1
                # remote sent something unexpected or local did not clear ok
                else:
                    self._send_nak()

            # finished 16 retries for control characters w/o success
            if not something_to_rx:
                self.delegate.x_buffer = bytes()
                self.write(CAN)
                self.write(CAN)
                self.write(CAN)
                self.delegate.xmodem_mode = False
                return -2

            # start receiving pages, or blocks
            trychar = 0
            len_page_plus_crc = bufsz + 5
            self._collect(len_page_plus_crc)

            # TIMEOUT, did not receive whole page in time, NAK to retry
            if len(self.delegate.x_buffer) != len_page_plus_crc:
                retrans -= 1
                self._send_nak()
                continue

            # todo: check the sequence numbers here, NAK if needed

            # whole page received, good CRC, ACK
            if self._check_crc():
                nseq = self.delegate.x_buffer[1]
                print('.'.format(nseq), end='')
                if not nseq % 25:
                    print('\n')
                self.write(ACK)
                retrans = MAXRETRANS
                whole_file += self.delegate.x_buffer[3:-2]
                self.delegate.x_buffer = bytes()
                continue
            # whole page received but bad CRC, NAK
            else:
                nseq = self.delegate.x_buffer[1]
                print('x{} '.format(nseq), end='')
                if not nseq % 25:
                    print('\n')
                retrans -= 1
                # too many consecutive fails for this page
                if not retrans:
                    print('exhausted page retries')
                    self.write(CAN)
                    self.write(CAN)
                    self.write(CAN)
                    self.delegate.xmodem_mode = False
                    return -3
                # still some fails allowed for this page
                self._send_nak()
                continue

    # get byte at indicated index
    def _inbyte(self, index):
        if len(self.delegate.x_buffer):
            return bytes([self.delegate.x_buffer[index]])
        return None

    # collect bytes which form page
    def _collect(self, minimum):
        end_time = time.time() + 1
        while time.time() < end_time:
            self.peripheral.waitForNotifications(0.05)
            # minimum = 1 when receiving CTRL chars (SOH, SOT...), > 1 else
            if len(self.delegate.x_buffer) >= minimum:
                return True
        return False

    # to start with a clean sheet after an error
    def _send_nak(self):
        print('x')
        NAK = b'\x15'
        self._collect_to_purge(1)
        self.delegate.x_buffer = bytes()
        self.write(NAK)

    # clean possible incoming full buffers
    def _collect_to_purge(self, during):
        end_time = time.time() + during
        while time.time() < end_time:
            self.peripheral.waitForNotifications(0.05)

    # skip SOH, SOT, sequence numbers and CRC of frame and calculate CRC
    def _check_crc(self):
        data = self.delegate.x_buffer[3:-2]
        received_crc_bytes = self.delegate.x_buffer[-2:]
        calculated_crc_int = crc16.crc16xmodem(data)
        calculated_crc_bytes = calculated_crc_int.to_bytes(2, byteorder='big')
        if calculated_crc_bytes == received_crc_bytes:
            return True
        else:
            return False

    # prevent garbage collector
    def __del__(self):
        pass

class LCBLEException(Exception):
    pass
