import pytest
import datetime
from mat.logger_controller_ble_cc26x2 import (
    LoggerControllerBLECC26X2,
    Delegate,
)


cmd_method = 'mat.logger_controller_ble_cc26x2.LoggerControllerBLECC26X2'\
             '.command'

_cmd_answer_method = 'mat.logger_controller_ble.LoggerControllerBLE'\
                     '._wait_for_command_answer'


@pytest.fixture
def fake_ble_factory(mocker):
    def patched_logger_controller(p=FakePeripheral, c='', c_a=''):
        mocker.patch('bluepy.btle.Peripheral', p)
        mocker.patch(cmd_method, return_value=c)
        mocker.patch(_cmd_answer_method, return_value=c_a)
        return LoggerControllerBLECC26X2
    return patched_logger_controller


class FakeChara:
    def write(self, data, withResponse=False):
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


class FakePeripheralEx(FakePeripheral):
    def connect(self, mac):
        raise AttributeError


class TestLoggerControllerBLECC26X2:
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
        d.set_file_mode(False)
        assert not d.file_mode
        d.set_file_mode(True)
        assert d.file_mode

    # test for open method, went ok
    def test_open_ok(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        assert lc_ble.peripheral

    # test for open method, went wrong
    def test_open_bad(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(p=FakePeripheralEx))('ff:ff:ff:ff:ff:ff')
        assert not lc_ble.open()

    # test for close method
    def test_close_ok(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        assert lc_ble.close()

    # test for close method, went wrong
    def test_close_bad(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())('ff:ff:ff:ff:ff:ff')
        assert not lc_ble.close()

    # test for a command which requires no answer
    def test_command_no_answer_required(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        lc_ble.characteristic = FakeChara()
        assert lc_ble._command('sleep') is None

    # test for a command which performs perfectly
    def test_command_answer_ok(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(c=[b'STS', b'0201']))('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        lc_ble.characteristic = FakeChara()
        assert lc_ble.command('STS') == [b'STS', b'0201']

    # test for parsing received command answer
    def test_command_answer_internal(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(c_a=b'STS\t\t\t0201'))('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        lc_ble.delegate.buffer = b'STS\t\t\t0201'
        assert lc_ble._wait_for_command_answer('STS') == b'STS\t\t\t0201'

    # test for listing logger files
    def test_list_files(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(c=[b'bean.lid', b'76']))('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        assert lc_ble.list_files() == {b'bean.lid': b'76'}

    # test for listing a logger containing no files
    def test_list_files_empty(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(c=[]))('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        assert lc_ble.list_files() == {}

    # test for getting logger time
    def test_get_time(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(c=[b'GTM', b'131999/12/12', b'11:12:13']))\
            ('ff:ff:ff:ff:ff:ff')
        lc_ble.open()
        expected = datetime.datetime(1999, 12, 12, 11, 12, 13)
        assert lc_ble.get_time() == expected

    # test for command provoking BLE error
    def test_command_exception(self, fake_ble_factory):
        with pytest.raises(ZeroDivisionError):
            lc_ble = (fake_ble_factory())('ff:ff:ff:ff:ff:ff')
            lc_ble._command = 1 / 0
            lc_ble.command()
