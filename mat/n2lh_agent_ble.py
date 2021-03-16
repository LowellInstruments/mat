import datetime
import json
import threading

from bluepy.btle import BTLEException, BTLEInternalError

from mat import logger_controller_ble
from mat.logger_controller_ble_dummy import EXC_CMD
from mat.logger_controller_ble_factory import LcBLEFactory
from mat.n2lx_utils import *
from mat.logger_controller import (
    STOP_CMD, STATUS_CMD, FIRMWARE_VERSION_CMD, LOGGER_INFO_CMD,
    CALIBRATION_CMD, SENSOR_READINGS_CMD, DO_SENSOR_READINGS_CMD,
    DEL_FILE_CMD, RUN_CMD, RWS_CMD, SWS_CMD, LOGGER_HSA_CMD_W,
    LOGGER_INFO_CMD_W, SET_TIME_CMD, REQ_FILE_NAME_CMD,
    SD_FREE_SPACE_CMD, RESET_CMD
)
from mat.logger_controller_ble import (
    is_a_li_logger, FORMAT_CMD,
    ERROR_WHEN_BOOT_OR_RUN_CMD, MOBILE_CMD, LOG_EN_CMD, UP_TIME_CMD,
    MY_TOOL_SET_CMD, CONFIG_CMD, ERR_MAT_ANS, WAKE_CMD
)


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
    return 1, '{} {} error'.format(AG_BLE_ERROR, s)


def _ok(s):
    return 0, '{} {}'.format(AG_BLE_OK, s)


def _ok_or_nok(rv: list, c: str):
    # rv: [b'STM', b'00']
    if rv[0] == c.encode():
        p = '' if len(rv) == 1 else rv[1].decode()
        return _ok('{} {}'.format(c, p))
    return _nok(c)


class AgentN2LH_BLE(threading.Thread):
    def __init__(self, q1, q2):
        """ creates an agent for simpler BLE logger controller """
        super().__init__()
        self.lc = None
        self.q_in = q1
        self.q_out = q2
        self.h = 0

    def _exc(self):
        self.q_out.put(AG_BLE_EXCEPTION)

    def _parse_n2lh_ble_incoming_frame(self, s):
        """ s: '<ag_ble_cmd> <args> <mac>' """
        cmd, *_ = s.split(' ', 1)
        fxn_map = {
            AG_BLE_CMD_HCI: self.set_hci,
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
            AG_BLE_CMD_EXCEPTION_GEN: self.exc_provoke,
            AG_BLE_END_THREAD: self.break_thread
        }
        fxn = fxn_map[cmd]
        # noinspection PyArgumentList
        return fxn(s)

    def loop_ag_ble(self):
        """ dequeues requests from AG_N2LH, queues back answers """
        while 1:
            _in = self.q_in.get()
            # _p('-> AG_BLE {}'.format(_in))
            _out = self._parse_n2lh_ble_incoming_frame(_in)
            # _p('<- AG_BLE {}'.format(_out))
            self.q_out.put(_out)

            # we can leave N2LH_BLE thread on demand
            if AG_BLE_END_THREAD in _out[1]:
                # _out: (0, 'AG_BLE_OK: ble_bye')
                break

    def run(self):
        try:
            self.loop_ag_ble()
            _p('AG_BLE: thread ends')

        except BTLEException:
            # ex: BLE connection LOST, tell remote N2LH_BASE agent
            # can simulate loss with a CMD or also can be spontaneous
            _p('<- AG_BLE caught exception')
            return self._exc()

    @staticmethod
    def scan(s):
        # s: scan 0 5
        _, h, t = s.split(' ')
        sr = logger_controller_ble.ble_scan(int(h), float(t))
        rv = ''
        for each in sr:
            rv += '{} {} '.format(each.addr, each.rssi)
        return _ok(rv.strip())

    @staticmethod
    def scan_li(s):
        # s: scan_li 0 5
        _, h, t = s.split(' ')
        sr = logger_controller_ble.ble_scan(int(h), float(t))
        rv = ''
        for each in sr:
            if is_a_li_logger(each.rawData):
                rv += '{} {} '.format(each.addr, each.rssi)
        return _ok(rv.strip())

    def set_hci(self, s):
        # s: set_hci 1
        _, h, = s.split(' ')
        f = '/sys/kernel/debug/bluetooth/hci{}'.format(h)
        if os.path.exists(f):
            # cut any current connection w/ different mac
            if self.lc:
                self.lc.close()
            self.h = h
            return _ok(AG_BLE_ANS_HCI_OK)
        return _nok(AG_BLE_ANS_HCI_ERR)

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

        # any kind of real or dummy logger
        lc = LcBLEFactory.generate(mac)
        self.lc = lc(mac, self.h)

        # connecting asked mac
        if self.lc.open():
            a = '{} {}'.format(AG_BLE_ANS_CONN_OK, mac)
            return _ok(a)
        return _nok(AG_BLE_ANS_CONN_ERR)

    def disconnect(self, _=None):
        # does not use any parameter such as 'mac'
        if self.lc and self.lc.close():
            return _ok(AG_BLE_ANS_DISC_OK)
        return _ok(AG_BLE_ANS_DISC_ALREADY)

    def get_time(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_GET_TIME)

        # rv: datetime object
        rv = self.lc.get_time()
        if type(rv) is not datetime.datetime:
            return _nok(AG_BLE_CMD_GET_TIME)
        s = rv.strftime('%Y/%m/%d %H:%M:%S')
        return _ok(s) if len(s) == 19 else _nok(AG_BLE_CMD_GET_TIME)

    def config(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_CONFIG)

        # s: 'config <config_str> <mac>'
        cfg_str = s[s.index(' ') + 1: s.rindex(' ')]
        cfg_dict = json.loads(cfg_str)
        rv = self.lc.send_cfg(cfg_dict)
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
            return _nok('bad cmd, maybe forgot mac?')
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
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_SET_TIME)

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

    def exc_provoke(self, s):
        # triggers except clause in  _parse_n2lh_ble_incoming_frame()
        _p('-> AG_BLE: sending cmd to provoke exception...')
        return self._cmd_ans(_mac_n_connect(s, self), EXC_CMD)

    # prevent same name as thread function run()
    def cmd_run(self, s):
        return self._cmd_ans(_mac_n_connect(s, self), RUN_CMD)

    # todo: check RWS, SWS, WHS, WLI work correctly
    def rws(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_RWS)

        # s: 'rws <rws_str> <mac>'
        rws_str = s[s.index(' ') + 1: s.rindex(' ')]
        rws_str = rws_str[:20]
        rv = self.lc.command(RWS_CMD, rws_str)
        if rv[0].decode() == RWS_CMD:
            return _ok(AG_BLE_CMD_RWS)
        return _nok(AG_BLE_CMD_RWS)

    def sws(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_SWS)

        # s: 'sws <sws_str> <mac>'
        sws_str = s[s.index(' ') + 1: s.rindex(' ')]
        sws_str = sws_str[:20]
        rv = self.lc.command(SWS_CMD, sws_str)
        if rv[0].decode() == SWS_CMD:
            return _ok(AG_BLE_CMD_SWS)
        return _nok(AG_BLE_CMD_SWS)

    def whs(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_WHS)

        # s: 'whs <whs_str> <mac>'
        whs_field = s[s.index(' ') + 1: s.rindex(' ')]
        rv = self.lc.command(LOGGER_HSA_CMD_W, whs_field)
        if rv[0].decode() == LOGGER_HSA_CMD_W:
            return _ok(AG_BLE_CMD_WHS)
        return _nok(AG_BLE_CMD_WHS)

    def wli(self, s):
        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_WLI)

        # s: 'wli <wli_str> <mac>'
        wli_field = s[s.index(' ') + 1: s.rindex(' ')]
        rv = self.lc.command(LOGGER_INFO_CMD_W, wli_field)
        if rv[0].decode() == LOGGER_INFO_CMD_W:
            return _ok(AG_BLE_CMD_WLI)
        return _nok(AG_BLE_CMD_WLI)

    def query(self, _):
        a = 'logger controller {}'
        if not self.lc:
            return _ok(a.format(AG_BLE_EMPTY))
        if not self.lc.per:
            return _ok(a.format(AG_BLE_EMPTY))
        return _ok(a.format(self.lc.per.getState()))

    def get_file(self, s):
        # s: 'get_file <file> <size> <mac>
        file, size = _sp(s, 1), _sp(s, 2)

        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_GET_FILE)

        # this involves both GET answer and xmodem_RX file
        fol = '/tmp'
        if self.lc.get_file(file, fol, size):
            a = '{} {} {} {}'.format(AG_BLE_CMD_GET_FILE, file, fol, size)
            return _ok(a)
        return _nok(AG_BLE_CMD_GET_FILE)

    def dwg_file(self, s):
        # s: 'dwg_file <file> <size> <mac>
        file, size = _sp(s, 1), _sp(s, 2)

        if not _mac_n_connect(s, self):
            return _nok(AG_BLE_CMD_DWG_FILE)

        # this involves both DWG answer and DWL file
        fol = '/tmp'
        if self.lc.dwg_file(file, fol, size, None):
            a = '{} {} {} {}'.format(AG_BLE_CMD_DWG_FILE, file, fol, size)
            return _ok(a)
        return _nok(AG_BLE_CMD_DWG_FILE)

    def close(self):
        return self.disconnect()
