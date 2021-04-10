import xmlrpc
from xmlrpc.client import Binary

from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import ble_scan
from mat.logger_controller_ble_factory import LcBLEFactory
from mat.xs_ble import xs_ble_check_ans_is_ok


def xs_get_client(url):
    # url: 'http://localhost:9000'
    xp = xmlrpc.client.ServerProxy(url, allow_none=True)
    return xp


class XS:
    """ XS: XML RPC server """

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

    @staticmethod
    def xs_ble_scan():
        sr = ble_scan(0)
        sr_f = [each_sr.addr for each_sr in sr]
        return sr_f

    def xs_ble_set_hci(self, hci_if: int):
        self.lc.hci_if = hci_if
        return 'hci set went ok'

    def xs_ble_connect(self, mac):
        self.lc = None
        lc_c = LcBLEFactory.generate(mac)
        self.lc = lc_c(mac)
        return self.lc.open()

    def xs_ble_disconnect(self):
        return self.lc.close()

    def xs_ble_get_mac_connected_to(self):
        return self.lc.address

    def xs_ble_cmd_status(self):
        ans = self.lc.command(STATUS_CMD)
        rv = xs_ble_check_ans_is_ok(ans)
        if not rv[0]:
            return rv[1]
        map_ans = {'0201': 'logger is stopped',
                   '0203': 'logger is delayed',
                   '0200': 'logger is running'}
        return map_ans[ans[1].decode()]



