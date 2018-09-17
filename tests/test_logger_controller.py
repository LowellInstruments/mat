from unittest.mock import patch
from unittest import TestCase
from serial import SerialException
from mat.logger_controller import LoggerController


COM_PORT = "1234"
COM_NAME = "COM" + COM_PORT
COM_VALUE = [[COM_NAME]]
TTY_NAME = "ttyACM0"
TTY_VALUE = [[TTY_NAME]]


class FakeExceptionSerial:
    def __init__(self, path, baud=9600):
        raise SerialException


class FakeSerial:
    close_count = 0

    def __init__(self, path, baud=9600):
        self.path = path
        self.baud = baud

    def close(self):
        FakeSerial.close_count += 1
        pass

    def reset_input_buffer(self):
        pass

    def write(self, *args):
        pass


class FakeSerialReader(FakeSerial):
    reads = [b'ERR']

    def __init__(self, path, baud=9600):
        super().__init__(path, baud)
        self.read_count = 0

    def read(self, count):
        result = self.reads[self.read_count % len(self.reads)]
        self.read_count += 1
        return result


class FakeSerialExceptionReader(FakeSerialReader):
    def read(self, count):
        raise SerialException


class FakeSerialErr(FakeSerialReader):
    reads = [b'\n', b'\r', b'E', b'RR 04', b'boom']


class FakeSerialSit(FakeSerialReader):
    reads = [b'\n', b'\r', b'S', b'IT 04', b'down']


class FakeSerialShortData(FakeSerialReader):
    reads = [b'\n', b'\r', b'S', b'IT 04', b'dow']


class FakeSerialRHS(FakeSerialReader):
    reads = [b'\n', b'\r', b'R', b'HS 04', b'down']


class TestLoggerController(TestCase):
    def test_create(self):
        assert LoggerController()

    def test_check_ports(self):
        controller = LoggerController()
        assert controller.check_ports() == []

    @patch('mat.logger_controller.grep',
           return_value=TTY_VALUE)
    @patch('mat.logger_controller.os.name', "posix")
    def test_check_ports_tty(self, grep):
        controller = LoggerController()
        assert controller.check_ports() == [TTY_NAME]

    @patch('mat.logger_controller.grep',
           return_value=COM_VALUE)
    @patch('mat.logger_controller.os.name', "nt")
    def test_check_ports_com(self, grep):
        controller = LoggerController()
        assert controller.check_ports() == [COM_PORT]

    @patch('mat.logger_controller.grep',
           return_value=COM_VALUE)
    @patch('mat.logger_controller.os.name', "unknown")
    def test_check_ports_unknown(self, grep):
        controller = LoggerController()
        with self.assertRaises(RuntimeError):
            controller.check_ports()

    @patch('mat.logger_controller.os.name', "unknown")
    def test_open_port(self):
        controller = LoggerController()
        with self.assertRaises(AttributeError):
            controller.open_port(com_port="1")

    @patch('mat.logger_controller.os.name', "posix")
    @patch('mat.logger_controller.Serial', FakeSerial)
    def test_open_port_on_posix(self):
        controller = LoggerController()
        assert controller.open_port(com_port="1")

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerial)
    @patch('mat.logger_controller.Serial.close', return_value=None)
    def test_open_port_on_nt(self, close):
        controller = LoggerController()
        assert controller.open_port(com_port="1")
        assert close.call_count == 0

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerial)
    def test_open_port_twice(self):
        controller = LoggerController()
        assert controller.open_port(com_port="1")
        close_count = FakeSerial.close_count
        assert controller.open_port(com_port="1")
        assert FakeSerial.close_count > close_count

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeExceptionSerial)
    def test_open_port_exception(self):
        controller = LoggerController()
        assert not controller.open_port(com_port="1")

    @patch('mat.logger_controller.os.name', "nt")
    def test_auto_connect(self):
        controller = LoggerController()
        assert not controller.auto_connect()

    @patch('mat.logger_controller.grep',
           return_value=COM_VALUE)
    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerial)
    def test_auto_connect_with_ports(self, grep):
        controller = LoggerController()
        assert controller.auto_connect()

    def test_empty_command(self):
        controller = LoggerController()
        with self.assertRaises(IndexError):
            controller.command()

    def test_simple_command_port_closed(self):
        controller = LoggerController()
        assert controller.command("SIT") is None

    def test_command_with_data_port_closed(self):
        controller = LoggerController()
        assert controller.command("WAIT", "1") is None

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerial)
    def test_sleep_command(self):
        controller = LoggerController()
        assert controller.open_port(com_port="1")
        assert controller.command("sleep") is None

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerialSit)
    def test_sit_command(self):
        controller = LoggerController()
        assert controller.open_port(com_port="1")
        assert controller.command("SIT") == "down"

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerialShortData)
    def test_short_command(self):
        controller = LoggerController()
        assert controller.open_port(com_port="1")
        with self.assertRaises(RuntimeError):
            controller.command("SIT")

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerialSit)
    def test_sit_command_with_callbacks(self):
        controller = LoggerController()
        controller.set_callback("tx", _do_nothing)
        controller.set_callback("rx", _do_nothing)
        assert controller.open_port(com_port="1")
        assert controller.command("SIT") == "down"

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerialErr)
    def test_err_command_with_callbacks(self):
        controller = LoggerController()
        controller.set_callback("tx", _do_nothing)
        controller.set_callback("rx", _do_nothing)
        assert controller.open_port(com_port="1")
        assert controller.command("SIT") is None

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerialExceptionReader)
    def test_exception_command(self):
        controller = LoggerController()
        assert controller.open_port(com_port="1")
        assert controller.command("SIT") is None

    @patch('mat.logger_controller.os.name', "nt")
    @patch('mat.logger_controller.Serial', FakeSerialRHS)
    def test_load_host_storage(self):
        controller = LoggerController()
        assert controller.open_port(com_port="1")
        assert controller.load_host_storage() is None


def _do_nothing(*args):
    pass
