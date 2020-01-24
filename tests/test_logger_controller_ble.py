import pytest
import bluepy.btle
import sys
import datetime
if sys.platform != 'win32':
    from mat.logger_controller_ble import (
        LoggerControllerBLE,
        Delegate
    )
    from tests._test_logger_controller_ble import (
        FakePeripheral,
        FakeCharacteristic,
    )


mac_ti = '80:6f:b0:ff:ff:ff'
mac_un = 'ff:ff:ff:ff:ff:ff'
cmd = 'mat.logger_controller_ble.LoggerControllerBLE.command'
w_a = 'mat.logger_controller_ble.LoggerControllerBLE._wait_for_command_answer'
_ls = 'mat.logger_controller_ble.LoggerControllerBLE._ls'


@pytest.fixture
def fake_ble_factory(mocker):
    def patched_logger_controller(p=FakePeripheral, m='', rv=''):
        mocker.patch('bluepy.btle.Peripheral', p)
        if m:
            mocker.patch(m, return_value=rv)
        # returns a LC_BLE class w/ 1 attribute + 1 method patched
        return LoggerControllerBLE
    return patched_logger_controller


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
class TestLoggerControllerBLECC26X2:
    def test_buffer_receive_notifications(self):
        d = Delegate()
        d.handleNotification(None, b'\n\rany_data\r\n')
        assert d.buffer == b'\n\rany_data\r\n'
        d.file_mode = True
        d.handleNotification(None, b'\n\rany_data\r\n')
        assert d.x_buffer == b'\n\rany_data\r\n'

    def test_buffer_clear(self):
        d = Delegate()
        d.buffer = b'\n\rany_data\r\n'
        d.x_buffer = b'\n\rany_data\r\n'
        d.clear_delegate_buffer()
        d.clear_delegate_x_buffer()
        assert d.buffer == b''
        assert d.x_buffer == b''

    # test switch between command and file mode
    def test_switch_file_mode(self):
        d = Delegate()
        assert not d.file_mode
        d.set_file_mode(False)
        assert not d.file_mode
        d.set_file_mode(True)
        assert d.file_mode

    def test_is_manufacturer_ti(self):
        assert LoggerControllerBLE.is_manufacturer_ti('80:6f:b0:')
        assert LoggerControllerBLE.is_manufacturer_ti('04:ee:03:')

    def test_is_manufacturer_microchip(self):
        assert LoggerControllerBLE.is_manufacturer_microchip('00:1e:c0:')

    def test_constructor(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(mac_ti)
        assert lc_ble

    def test_open_ok(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(mac_ti)
        lc_ble.open()
        assert lc_ble.u.peripheral

    def test_open_bad(self, fake_ble_factory):
        with pytest.raises(bluepy.btle.BTLEException):
            lc_ble = (fake_ble_factory())(mac_un)
            lc_ble.open()

    def test_close_ok(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(mac_ti)
        lc_ble.open()
        assert lc_ble.close()

    def test_close_bad(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(mac_ti)
        assert not lc_ble.close()

    def test_command_no_answer_required(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(mac_ti)
        lc_ble.open()
        lc_ble.characteristic = FakeCharacteristic()
        assert lc_ble._command('sleep') is None

    def test_command_yes_answer_required(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=w_a, rv=b'STS\t\t\t0201'))(mac_ti)
        lc_ble.open()
        lc_ble.characteristic = FakeCharacteristic()
        assert lc_ble._command('STS') is not None

    def test_command_answer_internal(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=w_a, rv=b'STS\t\t\t0201'))(mac_ti)
        lc_ble.open()
        lc_ble.delegate.buffer = b'STS\t\t\t0201'
        assert lc_ble._wait_for_command_answer('STS') == b'STS\t\t\t0201'

    def test_command_answer_shortcut(self, fake_ble_factory):
        lc_ble = (fake_ble_factory())(mac_ti)
        lc_ble.open()
        lc_ble.delegate.buffer = b'GET 00'
        assert lc_ble._shortcut_command_answer('GET')
        lc_ble.delegate.buffer = b'\x04\n\r'
        assert lc_ble._shortcut_command_answer('DIR')

    def test_get_time(self, fake_ble_factory):
        lc_ble = (fake_ble_factory(m=cmd, rv=[b'GTM', b'131999/12/12',
                                              b'11:12:13']))(mac_ti)
        lc_ble.open()
        expected = datetime.datetime(1999, 12, 12, 11, 12, 13)
        assert lc_ble.get_time() == expected

    def test_ls_lid(self, fake_ble_factory):
        _rv = ([b'bean.lid', b'76', b'hello.csv', b'10'], 0, dict())
        lc_ble = (fake_ble_factory(m=_ls, rv=_rv))(mac_ti)
        lc_ble.open()
        assert lc_ble.ls_lid() == {'bean.lid': 76}

    def test_ls_not_lid(self, fake_ble_factory):
        _rv = ([b'bean.lid', b'76', b'hello.csv', b'10'], 0, dict())
        lc_ble = (fake_ble_factory(m=_ls, rv=_rv))(mac_ti)
        lc_ble.open()
        assert lc_ble.ls_not_lid() == {'hello.csv': 10}
