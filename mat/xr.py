import time
import xmlrpc
from xmlrpc.client import Binary
from xmlrpc.server import SimpleXMLRPCServer

from mat.logger_controller import STATUS_CMD, STOP_CMD, FIRMWARE_VERSION_CMD
from mat.logger_controller_ble import ble_scan, is_a_li_logger, brand_ti, brand_microchip, brand_whatever
from mat.logger_controller_ble_factory import LcBLEFactory
from mat.xr_ble import xs_ble_check_ans_is_ok

XS_BLE_CMD_CONNECT = 'connect'
XS_BLE_CMD_DISCONNECT = 'disconnect'
XS_BLE_CMD_STATUS = 'status'
XS_BLE_CMD_STOP = 'stop'
XS_BLE_CMD_SCAN = 'scan'
XS_BLE_CMD_GFV = 'gfv'


class XS:
    """ XS: XML-RPC server """

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

    def _xs_simple_ble_cmd(self, c):
        ans = self.lc.command(c)
        rv = xs_ble_check_ans_is_ok(ans)
        if not rv[0]:
            return rv[1]
        # ex: send back '0203' or '2.8.00'
        return ans[1].decode()

    def xs_ble_cmd_status(self): return self._xs_simple_ble_cmd(STATUS_CMD)
    def xs_ble_cmd_stop(self): return self._xs_simple_ble_cmd(STOP_CMD)
    def xs_ble_cmd_gfv(self): return self._xs_simple_ble_cmd(FIRMWARE_VERSION_CMD)

    @staticmethod
    def xs_ble_scan(h, man):
        # sort scan results by RSSI: reverse=True, farther ones first
        sr = ble_scan(h)
        sr = sorted(sr, key=lambda x: x.rssi, reverse=False)
        rv = ''
        map_man = {'ti': brand_ti, 'microchip': brand_microchip}
        fxn = map_man.setdefault(man, brand_whatever)
        for each in sr:
            if is_a_li_logger(each.rawData) and fxn(each.addr):
                rv += '{} {} '.format(each.addr, each.rssi)
        return rv


def xr_ble_xml_rpc_server():

    server = SimpleXMLRPCServer(('localhost', 9000),
                                logRequests=True,
                                allow_none=True)

    # exposes methods not starting with '_'
    server.register_instance(XS())

    # server loop
    try:
        print('th_xs_ble: launched')
        server.serve_forever()

    except KeyboardInterrupt:
        print('th_xs_ble: killed')


def xr_ble_xml_rpc_client(url, q_cmd_in, sig):

    # url: 'http://localhost:9000'
    xc = xmlrpc.client.ServerProxy(url, allow_none=True)
    while 1:
        time.sleep(.1)

        while not q_cmd_in.empty():
            # c: ('scan', 0, 'all')
            c = q_cmd_in.get()

            # ends function, maybe to re-create w/ new url
            if c[0] == 'break':
                print('th_xb: bye')
                return
            # print('dequeuing ', c[0])

            # maps c[0] to server function before calling RPC
            map_c = {
                XS_BLE_CMD_SCAN: xc.xs_ble_scan,
                XS_BLE_CMD_CONNECT: xc.xs_ble_connect,
                XS_BLE_CMD_STATUS: xc.xs_ble_cmd_status,
                XS_BLE_CMD_DISCONNECT: xc.xs_ble_disconnect,
                XS_BLE_CMD_STOP: xc.xs_ble_cmd_stop,
                XS_BLE_CMD_GFV: xc.xs_ble_cmd_gfv,
            }

            # remote-procedure-calls function, signal answer back
            fxn = map_c[c[0]]
            a = fxn(*c[1:])
            sig.emit((c[0], a))
