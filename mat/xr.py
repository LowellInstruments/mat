import json
import os
import threading
import time
import xmlrpc
from xmlrpc.client import Binary
from xmlrpc.server import SimpleXMLRPCServer
from mat.logger_controller import STATUS_CMD, STOP_CMD, FIRMWARE_VERSION_CMD, TIME_CMD, LOGGER_INFO_CMD, \
    SD_FREE_SPACE_CMD, CALIBRATION_CMD, LOGGER_INFO_CMD_W, LOGGER_HSA_CMD_W, REQ_FILE_NAME_CMD, RESET_CMD, \
    DO_SENSOR_READINGS_CMD, DEL_FILE_CMD, SWS_CMD, RWS_CMD, RUN_CMD
from mat.logger_controller_ble import ble_scan, is_a_li_logger, brand_ti, brand_microchip, brand_whatever, MOBILE_CMD, \
    UP_TIME_CMD, LED_CMD, WAKE_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, LOG_EN_CMD, MY_TOOL_SET_CMD, FORMAT_CMD, SLOW_DWL_CMD
from mat.logger_controller_ble_factory import LcBLEFactory
import subprocess as sp


XR_DEFAULT_PORT = 9000
XR_PID_FILE = '/dev/shm/pid_xr'
XS_BREAK = 'break'
XS_BLE_CMD_CONNECT = 'connect'
XS_BLE_CMD_DISCONNECT = 'disconnect'
XS_BLE_CMD_DISCONNECT_FOR_SURE = 'disconnect_for_sure'
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
XS_BLE_CMD_RHS = 'rhs'
XS_BLE_CMD_WLI = 'wli'
XS_BLE_CMD_WHS = 'whs'
XS_BLE_CMD_RFN = 'rfn'
XS_BLE_CMD_MTS = 'mts'
XS_BLE_CMD_RST = 'rst'
XS_BLE_CMD_GDO = 'gdo'
XS_BLE_CMD_FRM = 'frm'
XS_BLE_CMD_DEL = 'del'
XS_BLE_CMD_TST = 'tst'
XS_BLE_CMD_SWS = 'sws'
XS_BLE_CMD_RUN = 'run'
XS_BLE_CMD_RWS = 'rws'
XS_BLE_CMD_DWG = 'dwg'
XS_BLE_CMD_SLW = 'slw'
XS_BLE_EXCEPTION = 'exception'


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

    def xs_ble_connect(self, mac, h):
        self.lc = None
        lc_c = LcBLEFactory.generate(mac)
        self.lc = lc_c(mac, hci_if=h)
        return self.lc.open()

    def xs_ble_disconnect(self):
        if self.lc:
            self.lc.close()
        self.lc = None
        return True

    @staticmethod
    def xs_ble_disconnect_for_sure():
        # really hard bluetooth reset
        cmd = 'systemctl stop bluetooth'
        _ = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        rv = _.returncode
        time.sleep(3)
        cmd = 'systemctl start bluetooth'
        _ = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        rv += _.returncode
        return rv == 0

    def xs_ble_get_mac_connected_to(self): return self.lc.address
    def xs_ble_cmd_stop(self): return self.lc.command(STOP_CMD)
    def xs_ble_cmd_wake(self): return self.lc.command(WAKE_CMD)
    def xs_ble_cmd_gfv(self): return self.lc.command(FIRMWARE_VERSION_CMD)
    def xs_ble_cmd_mbl(self): return self.lc.command(MOBILE_CMD)
    def xs_ble_cmd_utm(self): return self.lc.command(UP_TIME_CMD)
    def xs_ble_cmd_stm(self): return self.lc.sync_time()
    def xs_ble_cmd_status(self): return self.lc.command(STATUS_CMD)
    # only send status, we disconnect in STATUS answer parse
    def xs_ble_cmd_status_n_disconnect(self): return self.lc.command(STATUS_CMD)
    def xs_ble_cmd_led(self): return self.lc.command(LED_CMD)
    def xs_ble_cmd_ebr(self): return self.lc.command(ERROR_WHEN_BOOT_OR_RUN_CMD)
    def xs_ble_cmd_cfs(self): return self.lc.command(SD_FREE_SPACE_CMD)
    def xs_ble_cmd_rfn(self): return self.lc.command(REQ_FILE_NAME_CMD)
    def xs_ble_cmd_rst(self): return self.lc.command(RESET_CMD)
    def xs_ble_cmd_gdo(self): return self.lc.command(DO_SENSOR_READINGS_CMD)
    def xs_ble_cmd_frm(self): return self.lc.command(FORMAT_CMD)
    def xs_ble_cmd_del(self, file_name): return self.lc.command(DEL_FILE_CMD, file_name)
    def xs_ble_cmd_sws(self, my_s): return self.lc.command(SWS_CMD, my_s)
    def xs_ble_cmd_rws(self, my_s): return self.lc.command(RWS_CMD, my_s)
    def xs_ble_cmd_run(self): return self.lc.command(RUN_CMD)
    def xs_ble_cmd_mts(self): return self.lc.command(MY_TOOL_SET_CMD)
    def xs_ble_cmd_slw(self): return self.lc.command(SLOW_DWL_CMD)

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

    def xs_ble_cmd_rhs(self):
        tmo = self.lc.command(CALIBRATION_CMD, "TMO")
        tmr = self.lc.command(CALIBRATION_CMD, "TMR")
        tma = self.lc.command(CALIBRATION_CMD, "TMA")
        tmb = self.lc.command(CALIBRATION_CMD, "TMB")
        tmc = self.lc.command(CALIBRATION_CMD, "TMC")
        tmo = tmo[1].decode()[2:]
        tmr = tmr[1].decode()[2:]
        tma = tma[1].decode()[2:]
        tmb = tmb[1].decode()[2:]
        tmc = tmc[1].decode()[2:]
        return '{} {} {} {} {}'.format(tmo, tmr, tma, tmb, tmc)

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

    def xs_ble_cmd_wli(self, w):
        # w: ['SN1234569', 'CA1234', 'BA8007', 'MA1234ABC']
        for each in w:
            rv = self.lc.command(LOGGER_INFO_CMD_W, each)
            if rv != [b'WLI', b'00']:
                return False
        return True

    def xs_ble_cmd_whs(self, w):
        # w: (tmo, tmr, tma, tmb, tmc)
        for each in w:
            rv = self.lc.command(LOGGER_HSA_CMD_W, each)
            if rv != [b'WHS', b'00']:
                return False
        return True

    def xs_ble_cmd_dwg(self, file_name, file_size):
        # this '.' is MAT lib local folder, not the app
        return self.lc.dwg_file(file_name, '.', file_size)

    @staticmethod
    def xs_ble_scan(hci_if, man, t):
        # sort scan results by RSSI: reverse=True, farther ones first
        sr = ble_scan(hci_if, my_to=t)
        sr = sorted(sr, key=lambda x: x.rssi, reverse=False)
        rv = ''
        map_man = {'ti': brand_ti, 'microchip': brand_microchip}
        fxn = map_man.setdefault(man, brand_whatever)
        for each in sr:
            if is_a_li_logger(each.rawData) and fxn(each.addr):
                rv += '{} {} '.format(each.addr, each.rssi)
        return rv


def xr_ble_xml_rpc_server():

    server = SimpleXMLRPCServer(('localhost', XR_DEFAULT_PORT),
                                logRequests=True,
                                allow_none=True)

    # exposes methods not starting with '_'
    server.register_instance(XS())

    # server loop
    try:
        pid = os.getpid()
        with open(XR_PID_FILE, 'w') as f:
            f.write(str(pid))
        print('th_xrs_ble: launched, pid {}'.format(pid))
        server.serve_forever()

    except KeyboardInterrupt:
        print('th_xs_ble: killed')


def xr_ble_xml_rpc_client(url, q_cmd_in, sig):

    # url: 'http://localhost:<port>'
    xc = xmlrpc.client.ServerProxy(url, allow_none=True)
    print('th_xb: started with url {}'.format(url))

    while 1:
        time.sleep(.1)

        while not q_cmd_in.empty():
            # c: ('scan', 0, 'all')
            c = q_cmd_in.get()

            # ends function
            if c[0] == XS_BREAK:
                print('th_xb: bye')
                return
            # print('dequeuing ', c[0])

            # maps c[0] to server function before calling RPC
            map_c = {
                XS_BLE_CMD_SCAN: xc.xs_ble_scan,
                XS_BLE_CMD_CONNECT: xc.xs_ble_connect,
                XS_BLE_CMD_STATUS: xc.xs_ble_cmd_status,
                XS_BLE_CMD_DISCONNECT: xc.xs_ble_disconnect,
                XS_BLE_CMD_DISCONNECT_FOR_SURE: xc.xs_ble_disconnect_for_sure,
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
                XS_BLE_CMD_CFS: xc.xs_ble_cmd_cfs,
                XS_BLE_CMD_RHS: xc.xs_ble_cmd_rhs,
                XS_BLE_CMD_WLI: xc.xs_ble_cmd_wli,
                XS_BLE_CMD_WHS: xc.xs_ble_cmd_whs,
                XS_BLE_CMD_RFN: xc.xs_ble_cmd_rfn,
                XS_BLE_CMD_MTS: xc.xs_ble_cmd_mts,
                XS_BLE_CMD_RST: xc.xs_ble_cmd_rst,
                XS_BLE_CMD_GDO: xc.xs_ble_cmd_gdo,
                XS_BLE_CMD_FRM: xc.xs_ble_cmd_frm,
                XS_BLE_CMD_DEL: xc.xs_ble_cmd_del,
                XS_BLE_CMD_TST: xc.xs_ble_cmd_tst,
                XS_BLE_CMD_SWS: xc.xs_ble_cmd_sws,
                XS_BLE_CMD_RUN: xc.xs_ble_cmd_run,
                XS_BLE_CMD_RWS: xc.xs_ble_cmd_rws,
                XS_BLE_CMD_DWG: xc.xs_ble_cmd_dwg,
                XS_BLE_CMD_SLW: xc.xs_ble_cmd_slw,
            }

            # map command to remote-procedure-calls function
            fxn = map_c[c[0]]
            pars = (c[1:])

            # do function
            try:
                a = fxn(*pars)
                sig.emit((c[0], a))
            except xmlrpc.client.Fault as xcf:
                print('wow! xmlrpc client exception -> {}'.format(xcf))
                sig.emit((XS_BLE_EXCEPTION, c[0]))


# thread: local XML-RPC server, for testing
if __name__ == '__main__':
    th_xs_ble = threading.Thread(target=xr_ble_xml_rpc_server)
    th_xs_ble.start()
    print('th_main ends')
