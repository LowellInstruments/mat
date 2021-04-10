import xmlrpc
from xmlrpc.client import Binary

from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import ble_scan, is_a_li_logger, brand_ti, brand_microchip, brand_whatever
from mat.logger_controller_ble_factory import LcBLEFactory
from mat.xs_ble import xs_ble_check_ans_is_ok

XS_URL_LOCALHOST = 'http://localhost:9000'
XS_BLE_CMD_CONNECT = 'connect'
XS_BLE_CMD_DISCONNECT = 'disconnect'
XS_BLE_CMD_STATUS = 'status'
XS_BLE_CMD_STOP = 'stop'
XS_BLE_CMD_SCAN = 'scan'


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
        return ans[1].decode()

    def xs_ble_cmd_stop(self):
        ans = self.lc.command(STATUS_CMD)
        rv = xs_ble_check_ans_is_ok(ans)
        if not rv[0]:
            return rv[1]
        return 'logger stopped OK'

    @staticmethod
    def xs_ble_scan(h, man):
        # sort scan results by RSSI: reverse=True, farther ones first
        sr = ble_scan(0)
        sr = sorted(sr, key=lambda x: x.rssi, reverse=False)
        rv = ''
        map_man = {'ti': brand_ti, 'microchip': brand_microchip}
        fxn = map_man.setdefault(man, brand_whatever)
        for each in sr:
            if is_a_li_logger(each.rawData) and fxn(each.addr):
                rv += '{} {} '.format(each.addr, each.rssi)
        return rv
