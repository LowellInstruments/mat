import pytest
import sys
import datetime
if sys.platform != 'win32':
    from mat.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
    from mat.logger_controller_ble import Delegate


f_mac = 'ff:ff:ff:ff:ff:ff'
cmd = 'mat.logger_controller_ble_rn4020.LoggerControllerBLERN4020.command'
_wait_answer = 'mat.logger_controller_ble.LoggerControllerBLE'\
               '._wait_for_command_answer'


@pytest.fixture
def fake_ble_factory(mocker):
    def patched_logger_controller(p=FakePeripheral, m='', rv=''):
        mocker.patch('bluepy.btle.Peripheral', p)
        if m:
            mocker.patch(m, return_value=rv)
        return LoggerControllerBLERN4020
    return patched_logger_controller


class FakeCharacteristic:
    def __init__(self, index=0):
        self.valHandle = index

    def write(self, data, withResponse=False):
        pass


class FakeCharacteristicIndexable:
    def __getitem__(self, index):
        return FakeCharacteristic(index)


class FakeService:
    def getCharacteristics(self, which_char):
        return FakeCharacteristicIndexable()


class FakePeripheral:
    def __init__(self, mac):
        self.mac = mac

    def setDelegate(self, delegate_to_fxn):
        pass

    def writeCharacteristic(self, where, value):
        pass

    def disconnect(self):
        pass

    def status(self):
        return {'mtu': (240,)}

    def setMTU(self, value):
        pass

    def getServiceByUUID(self, uuid):
        return FakeService()


class FakePeripheralEx(FakePeripheral):
    def __init__(self, mac):
        raise AttributeError


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
class TestLoggerControllerRN4020:
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
        lc_ble = (fake_ble_factory())(f_mac)
        lc_ble.open()
        assert lc_ble.peripheral

    # test for open method, went wrong
    def test_open_bad(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(p=FakePeripheralEx))(f_mac)
        assert not lc_ble.open()

    # test for close method
    def test_close_ok(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(f_mac)
        lc_ble.open()
        assert lc_ble.close()

    # test for close method, went wrong
    def test_close_bad(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(f_mac)
        assert not lc_ble.close()

    # test for a command which requires no answer
    def test_command_no_answer_required(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(f_mac)
        lc_ble.open()
        lc_ble.characteristic = FakeCharacteristic()
        assert lc_ble._command('sleep') is None

    # test for a command which requires one answer
    def test_command_yes_answer_required(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=_wait_answer, rv=b'STS\t\t\t0201'))(f_mac)
        lc_ble.open()
        lc_ble.characteristic = FakeCharacteristic()
        assert lc_ble._command('STS') is not None

    # test for a command which performs perfectly
    def test_command_answer_ok(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=cmd, rv=[b'STS', b'0201']))(f_mac)
        lc_ble.open()
        lc_ble.characteristic = FakeCharacteristic()
        assert lc_ble.command('STS') == [b'STS', b'0201']

    # test for parsing received command answer
    def test_command_answer_internal(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=_wait_answer, rv=b'STS\t\t\t0201'))(f_mac)
        lc_ble.open()
        lc_ble.delegate.buffer = b'STS\t\t\t0201'
        assert lc_ble._wait_for_command_answer('STS') == b'STS\t\t\t0201'

    # test for listing logger files
    def test_list_files(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=cmd, rv=[b'bean.lid', b'76']))(f_mac)
        lc_ble.open()
        assert lc_ble.list_lid_files() == {'bean.lid': 76}

    # test for listing a logger containing no files
    def test_list_files_empty(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=cmd, rv=[]))(f_mac)
        lc_ble.open()
        assert lc_ble.list_lid_files() == {}

    # test for getting logger time
    def test_get_time(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=cmd, rv=[b'GTM', b'131999/12/12',
                                              b'11:12:13']))(f_mac)
        lc_ble.open()
        expected = datetime.datetime(1999, 12, 12, 11, 12, 13)
        assert lc_ble.get_time() == expected
