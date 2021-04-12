import json
import time
import xmlrpc
from xmlrpc.client import Binary
from xmlrpc.server import SimpleXMLRPCServer
from mat.logger_controller import STATUS_CMD, STOP_CMD, FIRMWARE_VERSION_CMD, TIME_CMD, LOGGER_INFO_CMD, \
    SD_FREE_SPACE_CMD
from mat.logger_controller_ble import ble_scan, is_a_li_logger, brand_ti, brand_microchip, brand_whatever, MOBILE_CMD, \
    UP_TIME_CMD, LED_CMD, WAKE_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, LOG_EN_CMD
from mat.logger_controller_ble_factory import LcBLEFactory


XS_BLE_CMD_CONNECT = 'connect'
XS_BLE_CMD_DISCONNECT = 'disconnect'
XS_BLE_CMD_STATUS = 'status'
XS_BLE_CMD_STATUS_N_DISCONNECT = 'status_n_disconnect'
XS_BLE_CMD_STOP = 'stop'
XS_BLE_CMD_SCAN = 'scan'
XS_BLE_CMD_GFV = 'gfv'
XS_BLE_CMD_CONFIG = 'config'
XS_BLE_CMD_GET_TIME = 'gtm'
XS_BLE_CMD_MBL = 'mbl'
XS_BLE_CMD_UPTIME = 'uptime'
XS_BLE_CMD_SET_TIME = 'stm'
XS_BLE_CMD_LED = 'leds'
XS_BLE_CMD_WAK = 'wake'
XS_BLE_CMD_EBR = 'ebr'
XS_BLE_CMD_DIR = 'dir'
XS_BLE_CMD_DIR_NON = 'dir_non_lid'
XS_BLE_CMD_RLI = 'rli'
XS_BLE_CMD_LOG = 'log'
XS_BLE_CMD_CFS = 'cfs'


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
        if self.lc:
            return self.lc.close()
        return True

    def xs_ble_get_mac_connected_to(self): return self.lc.address
    def xs_ble_cmd_stop(self): return self.lc.command(STOP_CMD)
    def xs_ble_cmd_wake(self): return self.lc.command(WAKE_CMD)
    def xs_ble_cmd_gfv(self): return self.lc.command(FIRMWARE_VERSION_CMD)
    def xs_ble_cmd_mbl(self): return self.lc.command(MOBILE_CMD)
    def xs_ble_cmd_utm(self): return self.lc.command(UP_TIME_CMD)
    def xs_ble_cmd_stm(self): return self.lc.sync_time()
    def xs_ble_cmd_status(self): return self.lc.command(STATUS_CMD)
    # only send status, we disconnect later in time
    def xs_ble_cmd_status_n_disconnect(self): return self.lc.command(STATUS_CMD)
    def xs_ble_cmd_led(self): return self.lc.command(LED_CMD)
    def xs_ble_cmd_ebr(self): return self.lc.command(ERROR_WHEN_BOOT_OR_RUN_CMD)
    def xs_ble_cmd_cfs(self): return self.lc.command(SD_FREE_SPACE_CMD)

    def xs_ble_cmd_rli(self):
        # all 4
        sn = self.lc.command(LOGGER_INFO_CMD, 'SN')
        ca = self.lc.command(LOGGER_INFO_CMD, 'CA')
        ba = self.lc.command(LOGGER_INFO_CMD, 'BA')
        ma = self.lc.command(LOGGER_INFO_CMD, 'MA')
        sn = sn[1].decode()[-7:]
        ca = ca[1].decode()[-4:]
        ba = ba[1].decode()[-4:]
        ma = ma[1].decode()[-7:]
        return '{} {} {} {}'.format(sn, ca, ba, ma)

    def xs_ble_cmd_gtm(self):
        ans = self.lc.get_time()
        if not ans:
            return None
        return ans.strftime('%Y/%m/%d %H:%M:%S')

    def xs_ble_cmd_config(self, cfg):
        if type(cfg) is str:
            cfg = json.loads(cfg)
        return self.lc.send_cfg(cfg)

    def xs_ble_cmd_dir(self):
        return self.lc.ls_lid()

    def xs_ble_cmd_dir_non(self):
        return self.lc.ls_not_lid()

    def xs_ble_cmd_log(self):
        return self.lc.command(LOG_EN_CMD)

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
                XS_BLE_CMD_STATUS_N_DISCONNECT: xc.xs_ble_cmd_status_n_disconnect,
                XS_BLE_CMD_CONFIG: xc.xs_ble_cmd_config,
                XS_BLE_CMD_GET_TIME: xc.xs_ble_cmd_gtm,
                XS_BLE_CMD_MBL: xc.xs_ble_cmd_mbl,
                XS_BLE_CMD_UPTIME: xc.xs_ble_cmd_utm,
                XS_BLE_CMD_SET_TIME: xc.xs_ble_cmd_stm,
                XS_BLE_CMD_LED: xc.xs_ble_cmd_led,
                XS_BLE_CMD_WAK: xc.xs_ble_cmd_wake,
                XS_BLE_CMD_EBR: xc.xs_ble_cmd_ebr,
                XS_BLE_CMD_DIR: xc.xs_ble_cmd_dir,
                XS_BLE_CMD_DIR_NON: xc.xs_ble_cmd_dir_non,
                XS_BLE_CMD_RLI: xc.xs_ble_cmd_rli,
                XS_BLE_CMD_LOG: xc.xs_ble_cmd_log,
                XS_BLE_CMD_CFS: xc.xs_ble_cmd_cfs
            }

            # remote-procedure-calls function, signal answer back
            fxn = map_c[c[0]]
            pars = (c[1:])
            a = fxn(*pars)
            sig.emit((c[0], a))
