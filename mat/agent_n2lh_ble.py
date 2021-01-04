import json
import threading

from mat import logger_controller_ble
from mat.agent_utils import *
from mat.logger_controller import STOP_CMD, STATUS_CMD, FIRMWARE_VERSION_CMD, LOGGER_INFO_CMD, \
    CALIBRATION_CMD, SENSOR_READINGS_CMD, DO_SENSOR_READINGS_CMD, RESET_CMD, SD_FREE_SPACE_CMD, REQ_FILE_NAME_CMD, \
    DEL_FILE_CMD, RUN_CMD, RWS_CMD, SWS_CMD, LOGGER_HSA_CMD_W, LOGGER_INFO_CMD_W, SET_TIME_CMD
from mat.logger_controller_ble import LoggerControllerBLE, is_a_li_logger, FORMAT_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, \
    MOBILE_CMD, LOG_EN_CMD, UP_TIME_CMD, MY_TOOL_SET_CMD, CONFIG_CMD, brand_ti, ERR_MAT_ANS, WAKE_CMD
import queue

from mat.logger_controller_ble_dummy import LoggerControllerBLEDummyCC26x2, LoggerControllerBLEDummyRN4020, \
    brand_testing_cc26x2, brand_testing_rn4020


def _p(s):
    print(s, flush=True)


def _stringify_dir_ans(_d_a):
    if _d_a == ERR_MAT_ANS.encode():
        return ERR_MAT_ANS
    # _d_a: {'file.lid': 2182}
    rv = ''
    for k, v in _d_a.items():
        rv += '{} {} '.format(k, v)
    if rv == '':
        rv = AG_BLE_ANS_DIR_EMPTY
    return rv.rstrip()


def _mac_n_connect(s, ag_ble):
    # s: STS <mac>
    mac = s.rsplit(' ', 1)[-1]
    rv = ag_ble.connect(mac)
    if rv[0] == 0:
        return mac
    return None


def _sp(s, i):
    return s.rsplit(' ')[i]


def _nok(s):
    return 1, '{} {}'.format(AG_BLE_ERROR, s)


def _ok(s):
    return 0, '{} {}'.format(AG_BLE_OK, s)


def _ok_or_nok(rv: list, c: str):
    # rv: [b'STM', b'00']
    if rv[0] == c.encode():
        p = '' if len(rv) == 1 else rv[1].decode()
        return _ok('{} {}'.format(c, p))
    return _nok(c)


class AgentN2LH_BLE(threading.Thread):
    def __init__(self, q1, q2, hci_if=0):
        """ creates an agent for simpler BLE logger controller """
        super().__init__()
        self.lc = None
        self.q_in = q1
        self.q_out = q2
        self.h = hci_if

    def _parse_n2lh_ble_incoming_frame(self, s):
        """ s: '<ag_ble_cmd> <args> <mac>' """
        cmd, *_ = s.split(' ', 1)
        fxn_map = {
            AG_BLE_CMD_STATUS: self.status,
            AG_BLE_CMD_WAK: self.wak,
            AG_BLE_CMD_CONNECT: self.connect,
            AG_BLE_CMD_DISCONNECT: self.disconnect,
            AG_BLE_CMD_GET_TIME: self.get_time,
            AG_BLE_CMD_SET_TIME: self.set_time,
            AG_BLE_CMD_LS_LID: self.ls_lid,
            AG_BLE_CMD_LS_NOT_LID: self.ls_not_lid,
            AG_BLE_CMD_STOP: self.stop,
            AG_BLE_CMD_QUERY: self.query,
            AG_BLE_CMD_SCAN: self.scan,
            AG_BLE_CMD_SCAN_LI: self.scan_li,
            AG_BLE_CMD_GET_FW_VER: self.get_fw_ver,
            AG_BLE_CMD_RLI: self.rli,
            AG_BLE_CMD_RHS: self.rhs,
            AG_BLE_CMD_FORMAT: self.format,
            AG_BLE_CMD_EBR: self.ebr,
            AG_BLE_CMD_MBL: self.mbl,
            AG_BLE_CMD_LOG_TOGGLE: self.log_en,
            AG_BLE_CMD_GSR: self.gsr,
            AG_BLE_CMD_GSR_DO: self.gsr_do,
            AG_BLE_CMD_RESET: self.reset,
            AG_BLE_CMD_UPTIME: self.uptime,
            AG_BLE_CMD_CFS: self.cfs,
            AG_BLE_CMD_RFN: self.rfn,
            AG_BLE_CMD_MTS: self.mts,
            AG_BLE_CMD_CONFIG: self.config,
            AG_BLE_CMD_DEL_FILE: self.del_file,
            AG_BLE_CMD_RUN: self.cmd_run,
            AG_BLE_CMD_RWS: self.rws,
            AG_BLE_CMD_SWS: self.sws,
            AG_BLE_CMD_WLI: self.wli,
            AG_BLE_CMD_WHS: self.whs,
            AG_BLE_CMD_GET_FILE: self.get_file,
            AG_BLE_CMD_DWG_FILE: self.dwg_file,
            AG_BLE_END_THREAD: self.break_thread
        }
        fxn = fxn_map[cmd]

        # noinspection PyArgumentList
        return fxn(s)

    def loop_ag_ble(self):
        """ receives requests from AG_N2LH and answers them """
        while 1:
            _in = self.q_in.get()
            # _p('>> AG_BLE {}'.format(_in))
            _out = self._parse_n2lh_ble_incoming_frame(_in)
            # _p('<< AG_BLE {}'.format(_out))
            self.q_out.put(_out)

            # we can leave N2LH_BLE thread on demand
            if AG_BLE_END_THREAD in _out[1]:
                # _out: (0, 'AG_BLE_OK: ble_bye')
                break

    def run(self):
        self.loop_ag_ble()
        _p('AG_BLE thread exits')

    @staticmethod
    def scan(s):
        # s: scan 0 5
        _, h, t = s.split(' ')
        sr = logger_controller_ble.ble_scan(int(0), float(t))
        rv = ''
        for each in sr:
            rv += '{} {} '.format(each.addr, each.rssi)
        return _ok(rv.strip())

    @staticmethod
    def scan_li(s):
        # s: scan_li 0 5
        _, h, t = s.split(' ')
        sr = logger_controller_ble.ble_scan(int(0), float(t))
        rv = ''
        for each in sr:
            if is_a_li_logger(each.rawData):
                rv += '{} {} '.format(each.addr, each.rssi)
        return _ok(rv.strip())

    @staticmethod
    def break_thread(_):
        return _ok(AG_BLE_END_THREAD)

    def connect(self, s):
        # s: 'connect <mac>' but it may be already
        mac = s.rsplit(' ', 1)[-1]
        if self.lc:
            a = self.lc.address
            if a == mac:
                if self.lc.per and self.lc.per.getState() == "conn":
                    return _ok(AG_BLE_ANS_CONN_ALREADY)

        # cut any current connection w/ different mac
        if self.lc:
            self.lc.close()

        # show and classify mac
        if brand_testing_cc26x2(mac):
            self.lc = LoggerControllerBLEDummyCC26x2(mac)
        elif brand_testing_rn4020(mac):
            self.lc = LoggerControllerBLEDummyRN4020(mac)
        elif brand_ti(mac):
            self.lc = LoggerControllerBLE(mac, self.h)
        else:
            # brand microchip, never tested w/ GUI
            assert False

        # connecting asked mac
        if self.lc.open():
            a = '{} {}'.format(AG_BLE_ANS_CONN_OK, mac)
            return _ok(a)
        return _nok(AG_BLE_ANS_CONN_ERR)

    def disconnect(self, _=None):
        # does not use any parameter
        if self.lc and self.lc.close():
            return _ok(AG_BLE_ANS_DISC_OK)
        return _ok(AG_BLE_ANS_DISC_ALREADY)

    def get_time(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_GET_TIME)

        rv = self.lc.get_time()
        # in case of get_time(), rv already a string
        if len(str(rv)) == 19:
            return _ok(str(rv))
        return _nok(AG_BLE_CMD_GET_TIME)

    def config(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_CONFIG)

        # '$' symbol as useful guard since <cfg> has spaces
        cfg = s.split('$')[1]
        rv = self.lc.send_cfg(json.loads(cfg))
        if rv[0].decode() == CONFIG_CMD:
            return _ok(AG_BLE_CMD_CONFIG)
        return _nok(AG_BLE_CMD_CONFIG)

    def rli(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_CONFIG)

        # read all RLI fields
        a = ''
        for _ in ('SN', 'CA', 'BA', 'MA'):
            rv = self.lc.command(LOGGER_INFO_CMD, _)
            a += '{} {} '.format(_, rv[1].decode())
        if ERR_MAT_ANS in a:
            return _nok(AG_BLE_CMD_RLI)
        return _ok(a.rstrip())

    def rhs(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_RHS)

        # read all RHS fields
        a = ''
        for _ in ('TMO', 'TMR', 'TMA', 'TMB', 'TMC'):
            rv = self.lc.command(CALIBRATION_CMD, _)
            a += '{} {} '.format(_, rv[1].decode())
        if ERR_MAT_ANS in a:
            return _nok(AG_BLE_CMD_RHS)
        return _ok(a.rstrip())

    def _cmd_ans(self, mac, c):
        # c: STATUS_CMD
        if not mac:
            return _nok('no mac in cmd format')
        rv = self.lc.command(c)
        return _ok_or_nok(rv, c)

    def status(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), STATUS_CMD)

    def wak(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), WAKE_CMD)

    def get_fw_ver(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), FIRMWARE_VERSION_CMD)

    def format(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), FORMAT_CMD)

    def ebr(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), ERROR_WHEN_BOOT_OR_RUN_CMD)

    def mbl(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), MOBILE_CMD)

    def log_en(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), LOG_EN_CMD)

    def gsr(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), SENSOR_READINGS_CMD)

    def gsr_do(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), DO_SENSOR_READINGS_CMD)

    def reset(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), RESET_CMD)

    def uptime(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), UP_TIME_CMD)

    def cfs(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), SD_FREE_SPACE_CMD)

    def rfn(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), REQ_FILE_NAME_CMD)

    def mts(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), MY_TOOL_SET_CMD)

    def set_time(self, s):
        # it's not simply sending SET_TIME_CMD
        rv = self.lc.sync_time()
        # rv: [b'STM', b'00']
        if rv[0].decode() == SET_TIME_CMD:
            return _ok(AG_BLE_CMD_SET_TIME)
        return _nok(AG_BLE_CMD_SET_TIME)

    def del_file(self, s):
        # s: 'del_file <filename> <mac>'
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_DEL_FILE)

        # delete the file
        name = s.split(' ')[1]
        rv = self.lc.command(DEL_FILE_CMD, name)
        if rv[0].decode() == DEL_FILE_CMD:
            return _ok(AG_BLE_CMD_DEL_FILE)
        return _nok(AG_BLE_CMD_DEL_FILE)

    def ls_lid(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_LS_LID)
        rv = self.lc.ls_lid()
        if type(rv) == dict:
            return _ok(_stringify_dir_ans(rv))
        return _nok(rv)

    def ls_not_lid(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_LS_NOT_LID)
        rv = self.lc.ls_not_lid()
        if type(rv) == dict:
            return _ok(_stringify_dir_ans(rv))
        return _nok(rv)

    def stop(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), STOP_CMD)

    # prevent same name as thread function run()
    def cmd_run(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), RUN_CMD)

    def rws(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), RWS_CMD)

    def sws(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), SWS_CMD)

    def whs(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), LOGGER_HSA_CMD_W)

    def wli(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), LOGGER_INFO_CMD_W)

    def query(self, _):
        a = 'AG_BLE: logger controller {}'
        if not self.lc:
            return _ok(a.format(AG_BLE_EMPTY))
        if not self.lc.per:
            return _ok(a.format(AG_BLE_EMPTY))
        return _ok(a.format(self.lc.per.getState()))

    def get_file(self, s):
        # s: 'get_file <file> <fol> <size> <mac>
        file, fol, size = _sp(s, 1), _sp(s, 2), _sp(s, 3)

        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_GET_FILE)

        # this involves both GET answer and xmodem_RX file
        if self.lc.get_file(file, fol, size):
            a = '{} {} {}'.format(AG_BLE_CMD_GET_FILE, file, size)
            return _ok(a)
        return _nok(AG_BLE_CMD_GET_FILE)

    def dwg_file(self, s):
        # s: 'dwg_file <file> <fol> <size> <mac>
        file, fol, size = _sp(s, 1), _sp(s, 2), _sp(s, 3)

        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_DWG_FILE)

        # this involves both DWG answer and DWL file
        if self.lc.dwg_file(file, fol, size):
            a = '{} {} {}'.format(AG_BLE_CMD_DWG_FILE, file, size)
            return _ok(a)
        return _nok(AG_BLE_CMD_DWG_FILE)

    def close(self):
        return self.disconnect()
