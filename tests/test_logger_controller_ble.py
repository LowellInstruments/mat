from contextlib import contextmanager
from unittest.mock import patch
from unittest import TestCase
from mat.logger_controller_ble import (
    LoggerControllerBLE,
    Delegate,
)
import datetime
import bluepy.btle as btle


class FakeData:
    def __init__(self, index):
        self.valHandle = index

    def write(self, data, withResponse=False):
        pass


class FakeDataIndexable:
    def __getitem__(self, index):
        return FakeData(index)


class FakeService:
    def getCharacteristics(self, charact):
        return FakeDataIndexable()


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
    def connect(self, mac):
        raise AttributeError


class TestLoggerControllerBLE(TestCase):

    # test for receiving BLE data
    def test_notification_to_buffers(self):
        d = Delegate()
        d.handleNotification(None, b'\n\rany_data\r\n')
        assert d.buffer == b'\n\rany_data\r\n'
        d.file_mode = True
        d.handleNotification(None, b'\n\rany_data\r\n')
        assert d.x_buffer == b'\n\rany_data\r\n'

    # test buffers can be cleared
    def test_buffer_clear(self):
        d = Delegate()
        d.buffer = b'\n\rany_data\r\n'
        d.x_buffer = b'\n\rany_data\r\n'
        d.clear_delegate_buffer()
        d.clear_delegate_x_buffer()
        assert d.buffer == b''
        assert d.x_buffer == b''

    # test switch between command and file mode
    def test_switch_to_file_mode(self):
        d = Delegate()
        assert not d.file_mode
        d.clear_file_mode()
        assert not d.file_mode
        d.set_file_mode()
        assert d.file_mode

    # test for open method, went ok
    def test_open_ok(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.peripheral

    # test for open method, went ok
    def test_open_bad(self):
        with _peripheral_exception_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            assert not lc_ble.open()

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
            assert not lc_ble.close()

    # test for a command which requires no answer
    def test_command_no_answer_required(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble._command('sleep') is None

    # test for a command which performs perfectly
    def test_command_answer_ok(self):
        with _command_answer_patch(b'STS\t\t\t0201'):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.command('STS') == [b'STS', b'0201']

    # test for parsing command answer
    def test_command_answer_internal(self):
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            lc_ble.delegate.buffer = b'STS\t\t\t0201'
            assert lc_ble._command_answer('STS') == b'STS\t\t\t0201'

    # test for listing logger files
    def test_list_files(self):
        with _command_patch([b'bean.lid', b'76']):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.list_files() == {b'bean.lid': b'76'}

    # test for listing an empty logger
    def test_list_files_empty(self):
        with _command_patch([]):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            assert lc_ble.list_files() == {}

    # test for getting logger time
    def test_get_time(self):
        with _command_patch([b'GTM', b'001999/12/12', b'11:12:13']):
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble.open()
            expected = datetime.datetime(1999, 12, 12, 11, 12, 13)
            assert lc_ble.get_time() == expected

    # test for command provoking BLE error
    def test_command_exception(self):
        def _command_exception():
            raise btle.BTLEException('')
        with _peripheral_patch():
            lc_ble = LoggerControllerBLE('ff:ff:ff:ff:ff:ff')
            lc_ble._command = _command_exception
            lc_ble.command()


# ----------------------------------
# context managers
# ----------------------------------

peripheral_class = 'bluepy.btle.Peripheral'
write_method = 'mat.logger_controller_ble.LoggerControllerBLE.ble_write'
cmd_method = 'mat.logger_controller_ble.LoggerControllerBLE.command'
_cmd_answer_m = 'mat.logger_controller_ble.LoggerControllerBLE._command_answer'


@contextmanager
def _command_patch(rv_cmd):
    with patch(peripheral_class, FakePeripheral):
        with patch(cmd_method, return_value=rv_cmd):
            yield


@contextmanager
def _command_answer_patch(rv_cmd_answer):
    with patch(peripheral_class, FakePeripheral):
        with patch(write_method):
            with patch(_cmd_answer_m, return_value=rv_cmd_answer):
                yield


@contextmanager
def _peripheral_patch():
    with patch(peripheral_class, FakePeripheral):
        yield


@contextmanager
def _peripheral_exception_patch():
    with patch(peripheral_class, FakePeripheralException):
        yield
