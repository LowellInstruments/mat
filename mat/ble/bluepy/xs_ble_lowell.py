import os
import platform
from xmlrpc.client import Binary
from xmlrpc.server import SimpleXMLRPCServer

from mat.ble.bleak_beta.bleak_utils import ble_scan_bleak
from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020
if platform.system() == 'Linux':
    from mat.ble.bluepy.bluepy_utils import (
        ble_linux_hard_reset,
        ble_scan_bluepy
    )

from mat.ble.bluepy.xc_ble_lowell import (
    XS_DEFAULT_PORT,
    xr_assert_api_or_die, XS_BLE_EXC_XS
)


class BLEXmlRpcServer:
    """ XS: Xml-rpc Server """

    def __init__(self):
        self.lc = None

    @staticmethod
    def xs_ping():
        """ check server is alive """
        return True

    @staticmethod
    def exception_test(msg):
        """ exception example """
        raise RuntimeError(msg)

    @staticmethod
    def _xs_send_bin(b):
        """ unpack, re-pack, send-back binary """
        data = b.data
        print('send_back_binary({!r})'.format(data))
        response = Binary(data)
        return response

    @staticmethod
    def _xs_send_none():
        return None

    def xs_client_entry_point(self, cmd_n_args: list):
        # returns function pointer from function string name
        # ex: client.xs_ble_cmd_sts() -> OK
        # ex: client.xs_ble_cmd_123() -> ERROR
        _c = cmd_n_args[0]
        xr_assert_api_or_die(_c, dir(self))
        _a = cmd_n_args[1:] if len(cmd_n_args) > 1 else []
        fxn = getattr(self, _c)
        return fxn(*_a)

    @staticmethod
    def xs_ble_cmd_scan(hci_if, t):
        if platform.system() == 'Linux':
            return ble_scan_bluepy(hci_if, t)
        return ble_scan_bleak()

    @staticmethod
    def xs_ble_cmd_scan_dummy(hci_if, t):
        d = {'11:22:33:44:55:66': -50}
        return d

    @staticmethod
    def xs_ble_cmd_disconnect_for_sure(): return ble_linux_hard_reset()

    def xs_ble_get_mac_connected_to(self): return self.lc.address
    def xs_ble_cmd_gfv(self): return self.lc.ble_cmd_gfv()
    def xs_ble_cmd_sts(self): return self.lc.ble_cmd_sts()
    def xs_ble_cmd_utm(self): return self.lc.ble_cmd_utm()
    def xs_ble_cmd_gtm(self): return self.lc.ble_cmd_gtm()
    def xs_ble_cmd_stm(self): return self.lc.ble_cmd_stm()
    def xs_ble_cmd_wak(self): return self.lc.ble_cmd_wak()
    def xs_ble_cmd_slw(self): return self.lc.ble_cmd_slw()
    def xs_ble_cmd_log(self): return self.lc.ble_cmd_log()
    def xs_ble_cmd_mbl(self): return self.lc.ble_cmd_mbl()
    def xs_ble_cmd_led(self): return self.lc.ble_cmd_led()
    def xs_ble_cmd_ebr(self): return self.lc.ble_cmd_ebr()
    def xs_ble_cmd_cfs(self): return self.lc.ble_cmd_cfs()
    def xs_ble_cmd_mts(self): return self.lc.ble_cmd_mts()
    def xs_ble_cmd_tst(self): return self.lc.ble_cmd_tst()
    def xs_ble_cmd_rfn(self): return self.lc.ble_cmd_rfn()
    def xs_ble_cmd_rst(self): return self.lc.ble_cmd_rst()
    def xs_ble_cmd_gdo(self): return self.lc.ble_cmd_gdo()
    def xs_ble_cmd_frm(self): return self.lc.ble_cmd_frm()
    def xs_ble_cmd_dir(self): return self.lc.ble_cmd_dir()
    def xs_ble_cmd_run(self): return self.lc.ble_cmd_run()
    def xs_ble_cmd_stp(self): return self.lc.ble_cmd_stp()
    def xs_ble_cmd_rhs(self): return self.lc.ble_cmd_rhs()
    def xs_ble_cmd_rli(self): return self.lc.ble_cmd_rli()
    def xs_ble_cmd_sws(self, s): return self.lc.ble_cmd_sws(s)
    def xs_ble_cmd_rws(self, s): return self.lc.ble_cmd_rws(s)
    def xs_ble_cmd_del(self, s): return self.lc.ble_cmd_del(s)
    def xs_ble_cmd_cfg(self, s): return self.lc.ble_cmd_cfg(s)
    def xs_ble_cmd_wli(self, w): return self.lc.ble_cmd_wli(w)
    def xs_ble_cmd_whs(self, w): return self.lc.ble_cmd_whs(w)
    def xs_ble_cmd_dwl(self, n, sig): return self.lc.ble_cmd_dwl(n, sig)
    def xs_ble_cmd_dwg(self, s, fol, n): return self.lc.ble_cmd_dwg(s, fol, n)

    def xs_ble_cmd_status_n_disconnect(self):
        rv = self.lc.ble_cmd_sts()
        if self.lc:
            self.lc.ble_cmd_disconnect()
        return rv

    def xs_ble_cmd_disconnect(self):
        if self.lc:
            return self.lc.close()

    def xs_ble_cmd_connect(self, mac, h):
        # todo > assert > only bluepy classes
        self.lc = LoggerControllerRN4020(mac)
        return self.lc.open()

    def xs_ble_bye(self):
        if self.lc:
            self.lc.close()
        print('XS told to say bye!')
        os._exit(0)

    # special command to test LC exceptions
    def xs_ble_exc_lc(self):
        return self.lc.ble_cmd_exc_lc()

    # special command to test XS exceptions
    @staticmethod
    def xs_ble_exc_xs():
        return XS_BLE_EXC_XS


class ExceptionXS(Exception):
    pass


def xs_run():
    xs = SimpleXMLRPCServer(('localhost', XS_DEFAULT_PORT),
                            logRequests=True, allow_none=True)

    # exposes methods NOT starting w/ '_'
    xs.register_instance(BLEXmlRpcServer())

    # loop: serve forever
    try:
        xs.serve_forever()

    except KeyboardInterrupt:
        print('th_xs: killed')

