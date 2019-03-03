from mat.logger_controller_usb import LoggerControllerUSB
import pytest
from mat.logger_controller import (
    SD_CAPACITY_CMD,
    TIME_CMD,
    SET_TIME_CMD,
    RUN_CMD,
    SENSOR_READINGS_CMD,
    CommunicationError
)
import re
from serial import SerialException
from numpy.testing import assert_array_almost_equal


EXPECTED_LOGGER_SETTINGS = {
    'TMP': True, 'ACL': True, 'MGN': True, 'TRI': 1, 'ORI': 1, 'BMR': 32,
    'BMN': 32, 'PRS': False, 'PHD': False, 'PRR': 16, 'PRN': 16}


GREP_RETURN = {'nt': [['COM10']],
               'posix': [['ttyACM0']],
               'dummy': [['dummy']],
               'not_found': None}


@pytest.fixture
def fake_serial_factory(mocker):
    def patched_logger_controller(response='',
                                  system='nt',
                                  subclass=FakeSerial):
        subclass.response = response
        mocker.patch('mat.logger_controller_usb.Serial', subclass)
        mocker.patch('mat.logger_controller_usb.os.name', system)
        mocker.patch('mat.logger_controller_usb.grep',
                     return_value=GREP_RETURN.get(system, None))
        return LoggerControllerUSB
    return patched_logger_controller


class FakeSerial:
    response = []

    def __init__(self, path, baud=9600):
        self.path = path
        self.baud = baud
        self.response_str = self._make_response_str()

    def read(self, count):
        result = self.response_str[:count]
        self.response_str = self.response_str[count:]
        return result

    def close(self):
        pass

    def reset_input_buffer(self):
        pass

    def write(self, *args):
        pass

    def _make_response_str(self):
        if type(self.response) == str:
            self.response = [self.response]
        return ''.join(self.response).encode('ibm437')


class FakeSerialException(FakeSerial):
    def __init__(self, *args):
        raise SerialException


class FakeSerialReadException(FakeSerial):
    def read(self, count):
        raise SerialException


def test_create():
    assert LoggerControllerUSB()


def test_open_port_on_posix(fake_serial_factory):
    logger_controller = fake_serial_factory(system='posix')
    with logger_controller() as controller:
        assert controller.is_connected


def test_open_port_on_nt(fake_serial_factory):
    logger_controller = fake_serial_factory(system='nt')
    with logger_controller() as controller:
        assert controller.is_connected


def test_open_port_on_unknown(fake_serial_factory):
    logger_controller = fake_serial_factory(system='dummy')
    with pytest.raises(RuntimeError):
        with logger_controller() as controller:
            pass


def test_open_port_not_found(fake_serial_factory):
    logger_controller = fake_serial_factory(system='not_found')
    with pytest.raises(RuntimeError):
        with logger_controller() as controller:
            pass


def test_open_port_exception(fake_serial_factory):
    logger_controller = fake_serial_factory(subclass=FakeSerialException)
    with pytest.raises(RuntimeError):
        with logger_controller() as controller:
            assert controller.is_connected


def test_empty_command(fake_serial_factory):
    logger_controller = fake_serial_factory()
    with logger_controller() as controller:
        with pytest.raises(CommunicationError):
            controller.command(TIME_CMD)


def test_get_sd_capacity(fake_serial_factory):
    expected = 3864064
    logger_controller = fake_serial_factory('CTS 0d00003864064KB')
    with logger_controller('COM10') as controller:
        query = controller.command(SD_CAPACITY_CMD)
        capacity = re.search('([0-9]+)KB', query).group(1)
        assert int(capacity) == expected


def test_command_with_port_closed(fake_serial_factory):
    logger_controller = fake_serial_factory('GTM 0512345')
    with logger_controller() as controller:
        controller.close()
        assert controller.command(TIME_CMD) is None


def test_sleep_command(fake_serial_factory):
    logger_controller = fake_serial_factory()
    with logger_controller() as controller:
        assert controller.command('sleep') is None


def test_short_command(fake_serial_factory):
    logger_controller = fake_serial_factory('GTM 051234')
    with logger_controller() as controller:
        with pytest.raises(CommunicationError):
            controller.command(TIME_CMD)


def test_receive_err(fake_serial_factory):
    logger_controller = fake_serial_factory('ERR 00')
    with logger_controller() as controller:
        response = controller.command(TIME_CMD)
        assert response is None


def test_partial_response(fake_serial_factory):
    logger_controller = fake_serial_factory('GT')
    with logger_controller() as controller:
        with pytest.raises(CommunicationError):
            controller.command(TIME_CMD)


def test_two_parameter_command(fake_serial_factory):
    logger_controller = fake_serial_factory('STM 00')
    with logger_controller() as controller:
        controller.command(SET_TIME_CMD, '132019/03/01 16:47:51')


def test_delay_command(fake_serial_factory, mocker):
    sleep_mock = mocker.Mock()
    mocker.patch('mat.logger_controller_usb.time.sleep', sleep_mock)
    logger_controller = fake_serial_factory('RUN 00')
    with logger_controller() as controller:
        controller.command(RUN_CMD)
        sleep_mock.assert_called_with(2)


def test_read_raised_serial_exception(fake_serial_factory):
    logger_controller = fake_serial_factory(subclass=FakeSerialReadException)
    with logger_controller() as controller:
        response = controller.command(TIME_CMD)
        assert response is None

def test_open_already_opened_port(fake_serial_factory):
    logger_controller = fake_serial_factory()
    with logger_controller() as controller:
        controller.open()
        assert controller.is_connected is True

def test_get_sensor_readings(fake_serial_factory):
    reply = 'GSR 28368924f10af7eeff97026b03b9fe9e0f3f060000\r\n' + \
            'RHS 00' * 10
    logger_controller = fake_serial_factory(reply)
    with logger_controller() as controller:
        response = controller.get_sensor_readings()
        #TODO add an assert


def test_get_logger_settings_empty(fake_serial_factory):
    reply = 'GLS 00'
    logger_controller = fake_serial_factory(reply)
    with logger_controller() as controller:
        response = controller.get_logger_settings()
        assert response == {}


def test_get_logger_settings(fake_serial_factory):
    reply = 'GLS 1E010101010001002020000000101000'
    logger_controller = fake_serial_factory(reply)
    with logger_controller() as controller:
        response = controller.get_logger_settings()
        assert response == EXPECTED_LOGGER_SETTINGS


def test_callback(fake_serial_factory, mocker):
    logger_controller = fake_serial_factory('GTM 0512345')
    callback_target = mocker.Mock()
    expected = [mocker.call('GTM 00'), mocker.call('GTM 0512345')]
    with logger_controller() as controller:
        controller.set_callback('tx', callback_target)
        controller.set_callback('rx', callback_target)
        response = controller.command(TIME_CMD)
        callback_target.assert_has_calls(expected, any_order=False)
        assert callback_target.call_count == 2
        assert response == '12345'
