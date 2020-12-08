from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import FAKE_MAC_RN4020
from tests._lc_ble_dummy import LoggerControllerBLEDummyRN4020


# how to test this with coverage:
# python3 -m pytest
#       tests/test_lc_ble_dummy_rn4020.py
#       --cov tests.lc_ble_dummy_rn4020
#       --cov-report=html:<output_dir>


class TestLCBLEDummyRN4020:
    mac = FAKE_MAC_RN4020

    def test_constructor(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        assert lc.type

    def test_open(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        assert lc.type

    def test_ble_write(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        assert lc.type
        lc.ble_write('whatever_data')

    def test_get_file(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        assert lc.type
        rv = lc.get_file(lc, 'fake_file', 'fake_fol', 1234)
        assert rv

    def test_get_type(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        assert lc.get_type() == lc.type

    def test_close(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.close()
        assert rv
        assert not lc.type

    def test_purge(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        lc.purge()

    def test_xmd_rx_n_save(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.xmd_rx_n_save(lc, 'fake_file', 'fake_fol', 1234)
        assert rv

    def test_get_time(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.get_time()
        assert rv == '2020/12/31 12:34:56'

    def test_ls_lid(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.ls_lid()
        print(rv)
        assert rv == {'a.lid': '1234'}

    def test_ls_not_lid(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.ls_not_lid()
        assert rv == {'MAT.cfg': '101'}

    def test_send_cfg(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.send_cfg('my_cfg')
        # does not exist for RN4020 loggers
        assert not rv

    def test_send_btc(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.send_btc()
        assert rv == 'BTC 00T,0006,0000,0064'

    def test_dwg_file(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        rv = lc.dwg_file('fake_file', 'fake_fol', 1234)
        # does not exist for RN4020 loggers
        assert not rv

    def test_command_status(self):
        lc = LoggerControllerBLEDummyRN4020(self.mac)
        lc.open()
        assert lc.command(STATUS_CMD) == _rv_cmd_generic(STATUS_CMD)


def _rv_cmd_generic(*args):
    return args[0].encode(), b'00'


