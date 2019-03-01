from mat.logger_controller_usb import LoggerControllerUSB
import pytest
from mat.logger_controller import (
    SD_CAPACITY_CMD,
    TIME_CMD
)
import re
from serial import SerialException


GREP_RETURN = {'nt': [['COM10']], 'posix': [['ttyACM0']]}


@pytest.fixture
def fake_serial_factory(mocker):
    def patched_logger_controller(response='',
                                  system='nt',
                                  subclass=FakeSerial):
        subclass.response = response
        mocker.patch('mat.logger_controller_usb.Serial', subclass)
        mocker.patch('mat.logger_controller_usb.os.name', system)
        mocker.patch('mat.logger_controller_usb.grep',
                     return_value=GREP_RETURN[system])
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


def test_create():
    assert LoggerControllerUSB()


def test_open_port_on_posix(fake_serial_factory):
    logger_controller = fake_serial_factory(system='posix')
    with logger_controller() as controller:
        pass


def test_open_port_on_nt(fake_serial_factory):
    logger_controller = fake_serial_factory(system='nt')
    with logger_controller() as controller:
        pass


def test_open_port_exception(fake_serial_factory):
    logger_controller = fake_serial_factory(subclass=FakeSerialException)
    with pytest.raises(RuntimeError):
        with logger_controller() as controller:
            pass


def test_empty_command(fake_serial_factory):
    logger_controller = fake_serial_factory()
    with logger_controller() as controller:
        with pytest.raises(RuntimeError):
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
        with pytest.raises(RuntimeError):
            controller.command(TIME_CMD)

def test_receive_err(fake_serial_factory):
    logger_controller = fake_serial_factory('ERR')
    with logger_controller() as controller:
        controller.command(TIME_CMD)

