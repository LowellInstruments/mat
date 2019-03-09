from contextlib import contextmanager
from unittest.mock import patch, Mock
from unittest import TestCase
from mat.logger_controller_ble import (
    LoggerControllerBLE,
    Delegate,
    LCBLEException,
)


class FakeOutStream:
    def seek(self, a, b):
        pass

    def tell(self):
        return 12345

    def truncate(self, size):
        pass


class FakeOutStreamTellIsWrong(FakeOutStream):
    def tell(self):
        return 0


class FakeData:
    def __init__(self, index):
        self.valHandle = index

    def write(self, data, withResponse=False):
        pass


class FakeDataException(FakeData):
    def write(self, data, withResponse=False):
        raise LCBLEException


class FakeDataIndexable:
    def __getitem__(self, index):
        return FakeData(index)


class FakeDataIndexableException(FakeDataIndexable):
    def __getitem__(self, index):
        return FakeDataException(index)


class FakeService:
    def getCharacteristics(self, charact):
        return FakeDataIndexable()


class FakeServiceException(FakeService):
    def getCharacteristics(self, charact):
        return FakeDataIndexableException()


class FakeDelegateAscii:

    def __init__(self):
        self.xmodem_mode = False

    def handleNotification(self, handle, data):
        pass


class FakePeripheral:
    def __init__(self):
        pass

    def connect(self, mac):
        self.mac = mac

    def setDelegate(self, delegate_to_fxn):
        pass

    def writeCharacteristic(self, where, value):
        pass

    def waitForNotifications(self, value):
        return True

    def disconnect(self):
        pass

    def getServiceByUUID(self, uuid):
        return FakeService()


class FakePeripheralException(FakePeripheral):
    def getServiceByUUID(self, uuid):
        return FakeServiceException()


class FakePeripheralCmdTimeout(FakePeripheral):
    def waitForNotifications(self, value):
        return False


class TestLoggerControllerBLE(TestCase):

    # test for parsing while in ascii mode
    def test_read_line_no_read_buffer(self):
        self.assertRaises(IndexError, Delegate().read_line)

    # test for parsing while in ascii mode
    def test_read_line_read_buffer(self):
        d = Delegate()
        d.handleNotification(None, b'\n\rany_ascii_string\r\n')
        assert d.read_line() == b'any_ascii_string'

    # test buffer is not string but bytes, changed from python v2 to v3
    def test_buffer_is_bytes_not_str(self):
        d = Delegate()
        d.buffer = ''
        d.xmodem_mode = False
        d.handleNotification(None, b'\n\rignored_ascii_string\r\n')
        assert type(d.buffer) is bytes

    # test x_buffer collects xmodem bytes properly
    def test_x_buffer_collects(self):
        d = Delegate()
        d.xmodem_mode = True
        d.handleNotification(None, b'thing_received')
        assert d.x_buffer == b'thing_received'

    # test for open method
    def test_open(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.peripheral

    # test for close method
    def test_close_ok(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.close()

    # test for close method
    def test_close_not_ok(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.peripheral = None
            assert not lc_ble.close()

    # test for a command which requires no answer
    def test_command_no_answer_required(self):
        with _command_patch(None, ''):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.command('sleep', None) is None

    # test for a command which requires answer but timeouts
    def test_command_timeout(self):
        with _command_patch_timeout():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            self.assertRaises(LCBLEException, lc_ble.command, 'STS', None)

    # test for a command which performs perfectly
    def test_command_answer_ok(self):
        with _command_patch(True, b'STP'):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.command('STP') == b'STP'

    # test for exception when logger answering 'INV' to a command
    def test_command_answer_inv(self):
        with _command_patch(True, b'INV'):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            self.assertRaises(LCBLEException, lc_ble.command, 'STS')

    # test for exception when logger answering 'ERR' to a command
    def test_command_answer_err(self):
        with _command_patch(True, b'ERR'):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            self.assertRaises(LCBLEException, lc_ble.command, 'STS')

    # test for a control_command to RN4020 which performs perfectly
    def test_control_command_answer_ok(self):
        with _command_patch(True, b'CMDAOKMLDP'):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.control_command('data_X') == 'CMDAOKMLDP'

    # test for a control_command to RN4020 with new fw which does not goes well
    def test_control_command_answer_wrong(self):
        with _command_patch_timeout():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.control_command('data_X') == 'DIDNOT'

    # test for writing characteristics, used by command(), must do nothing
    def test_write(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            lc_ble.write('hello')

    # test for the special command 'DIR' when logger answers wrong
    def test_list_files_answer_wrong(self):
        with _command_patch(True, b'file_with_no_size.fil'):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            self.assertRaises(LCBLEException, lc_ble.list_files)

    # test for command 'DIR' when logger answers timeouts
    def test_list_files_answer_timeout(self):
        with _command_patch_timeout():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            self.assertRaises(LCBLEException, lc_ble.list_files)

    # test for command 'DIR' when logger answers perfectly but empty list
    def test_list_files_answer_empty(self):
        with _command_patch(True, b'\x04'):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.list_files() == []

    # test for command 'DIR' when logger answers a populated file list
    def test_list_files_answer_ok(self):
        rl_answers = Mock(side_effect=[b'one.h\t12', b'two.dat\t2345', b'\x04'])
        with _command_patch_dir(True, rl_answers):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.list_files() == [('one.h', 12), ('two.dat', 2345)]

    # test for xmodem mode, get control character
    def test_xmodem_inbyte(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            lc_ble.delegate.x_buffer = b'\x04\xff\x02'
            assert lc_ble._inbyte(0) == b'\x04'
            assert lc_ble._inbyte(2) == b'\x02'
            lc_ble.delegate.x_buffer = b''
            assert lc_ble._inbyte(100) is None

    # test for xmodem when collecting bytes from a file
    def test_xmodem_collect(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            lc_ble.delegate.x_buffer = b'\x04\xff\x02'
            assert lc_ble._collect(3)
            assert not lc_ble._collect(4)

    # test for xmodem to collect data for x secs to empty peripheral buffer
    def test_xmodem_collect_to_purge(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble._collect_to_purge(2) is None

    # test for xmodem to send nak
    def test_xmodem_send_nak(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble._send_nak() is None

    # test for xmodem to check CRC of something currently received
    def test_xmodem_check_crc(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            # recall first 3 bytes are not part of CRC in xmodem
            frame_wrong_no_crc = b'\xff\xff\xff\x03\x04\x05\x06\x07\x08\x09'
            lc_ble.delegate.x_buffer = frame_wrong_no_crc
            assert not lc_ble._check_crc()
            frame_ok_w_crc = b'\xff\xff\xff\x03\x04\x05\x06\x07\x08\x09\x47\xfd'
            lc_ble.delegate.x_buffer = frame_ok_w_crc
            assert lc_ble._check_crc()


# ----------------------------------
# context managers
# ----------------------------------

peripheral_class = 'bluepy.btle.Peripheral'
lc_ble_write_method = 'mat.logger_controller_ble.LoggerControllerBLE.write'
d_in_waiting_property = 'mat.logger_controller_ble.Delegate.in_waiting'
d_read_line_method = 'mat.logger_controller_ble.Delegate.read_line'


@contextmanager
def _peripheral_patch():
    with patch(peripheral_class, FakePeripheral):
        yield


@contextmanager
def _command_patch(rv_in_waiting, rv_read_line):
    with patch(peripheral_class, FakePeripheral):
        with patch(lc_ble_write_method):
            with patch(d_in_waiting_property, return_value=rv_in_waiting):
                with patch(d_read_line_method, return_value=rv_read_line):
                    yield


# this one provides different answers on successive calls of read_line()
@contextmanager
def _command_patch_dir(rv_in_waiting, rl_method):
    with patch(peripheral_class, FakePeripheral):
        with patch(lc_ble_write_method):
            with patch(d_in_waiting_property, return_value=rv_in_waiting):
                with patch(d_read_line_method, rl_method):
                    yield


# @contextmanager
# def _command_patch_get(rv_in_waiting, rv_read_line):
#     with _command_patch(rv_in_waiting, rv_read_line):
#             yield


@contextmanager
def _command_patch_timeout():
    with patch(peripheral_class, FakePeripheralCmdTimeout):
        with patch(lc_ble_write_method):
            yield


@contextmanager
def _write_char_exception_patch():
    with patch(peripheral_class, FakePeripheralException):
        yield
