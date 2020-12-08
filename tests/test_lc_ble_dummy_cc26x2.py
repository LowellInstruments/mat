from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import FAKE_MAC_CC26X2
from tests._lc_ble_dummy import LoggerControllerBLEDummyCC26x2


# how to test this with coverage:
# python3 -m pytest
#       tests/test_lc_ble_dummy_cc26x2.py
#       --cov tests.lc_ble_dummy_cc26x2
#       --cov-report=html:<output_dir>


class TestLCBLEDummyCC26X2:
    mac = FAKE_MAC_CC26X2

    def test_constructor(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        assert lc.type

    def test_open(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        assert lc.type

    def test_ble_write(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        assert lc.type
        lc.ble_write('whatever_data')

    def test_get_file(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        assert lc.type
        rv = lc.get_file(lc, 'fake_file', 'fake_fol', 1234)
        assert rv

    def test_get_type(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        assert lc.get_type() == lc.type

    def test_close(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.close()
        assert rv
        assert not lc.type

    def test_purge(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        lc.purge()

    def test_xmd_rx_n_save(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.xmd_rx_n_save(lc, 'fake_file', 'fake_fol', 1234)
        assert rv

    def test_get_time(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.get_time()
        assert rv == '2020/12/31 12:34:56'

    def test_ls_lid(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.ls_lid()
        print(rv)
        assert rv == {'a.lid': '1234'}

    def test_ls_not_lid(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.ls_not_lid()
        assert rv == {'MAT.cfg': '101'}

    def test_send_cfg(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.send_cfg('my_cfg')
        assert rv == [b'CFG', b'00']

    def test_send_btc(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.send_btc()
        # does not exist for CC26x2 loggers
        assert not rv

    def test_dwg_file(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        rv = lc.dwg_file('fake_file', 'fake_fol', 1234)
        assert rv

    def test_command_status(self):
        lc = LoggerControllerBLEDummyCC26x2(self.mac)
        lc.open()
        assert lc.command(STATUS_CMD) == _rv_cmd_generic(STATUS_CMD)


def _rv_cmd_generic(*args):
    return args[0].encode(), b'00'
