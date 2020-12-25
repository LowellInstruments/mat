from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import FAKE_MAC_RN4020
from mat.logger_controller_ble_dummy import LoggerControllerBLEDummyRN4020, FAKE_TIME, no_cmd_in_logger


# how to test this with coverage:
# python3 -m pytest
#       tests/test_lc_ble_dummy_rn4020.py
#       --cov tests.lc_ble_dummy_rn4020
#       --cov-report=html:<output_dir>


mac = FAKE_MAC_RN4020


class TestLCBLEDummyRN4020:

    def test_constructor(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        assert lc.type

    def test_open(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        assert lc.type

    def test_ble_write(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        assert lc.type
        lc.ble_write('whatever_data')

    def test_get_file(self):
        # don't emulate dummy downloads
        assert True

    def test_get_type(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        assert lc.get_type() == lc.type

    def test_close(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.close()
        assert rv
        assert not lc.type

    def test_purge(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        lc.purge()

    def test_xmd_rx_n_save(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.xmd_rx_n_save(lc, 'fake_file', 'fake_fol', 1234)
        assert rv

    def test_get_time(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.get_time()
        # this is a string because of get_time()
        assert rv == FAKE_TIME

    def test_ls_lid(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.ls_lid()
        assert type(rv) == dict

    def test_ls_not_lid(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.ls_not_lid()
        assert rv == {'MAT.cfg': '101'}

    def test_send_cfg(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.send_cfg(dict())
        # does not exist for RN4020 loggers
        assert rv == no_cmd_in_logger(lc)

    def test_send_btc(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.send_btc()
        assert rv == 'CMD\r\nAOK\r\nMLDP'

    def test_dwg_file(self):
        lc = LoggerControllerBLEDummyRN4020(mac)
        lc.open()
        rv = lc.dwg_file('fake_file', 'fake_fol', 1234)
        # does not exist for RN4020 loggers
        assert rv == no_cmd_in_logger(lc)

    def test_cmd_status(self): _test_cmd_generic(STATUS_CMD, mac)


def _test_cmd_generic(s, mac):
    lc = LoggerControllerBLEDummyRN4020(mac)
    lc.open()
    assert s.encode() in lc.command(s)
