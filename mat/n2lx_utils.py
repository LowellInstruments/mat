import os
import subprocess as sp
# requires 'python-crontab' package to be installed
from crontab import CronTab

from mat.utils import linux_is_rpi

AG_BLE_OK = 'AG_BLE_OK:'
AG_BLE_ERROR = 'AG_BLE_ERROR:'
AG_BLE_EXCEPTION = 'AG_BLE_EXCEPTION:'

AG_BLE_CMD_HCI = 'set_hci'
AG_BLE_CMD_STATUS = 'status'
AG_BLE_CMD_CONNECT = 'connect'
AG_BLE_CMD_DISCONNECT = 'disconnect'
AG_BLE_CMD_GET_TIME = 'get_time'
AG_BLE_CMD_SET_TIME = 'set_time'
AG_BLE_CMD_GET_FW_VER = 'get_fw_ver'
AG_BLE_CMD_LS_LID = 'ls_lid'
AG_BLE_CMD_LS_NOT_LID = 'ls_not_lid'
AG_BLE_CMD_EXCEPTION_GEN = 'ble_exc_cmd'
AG_BLE_CMD_HW_TEST = '#T1'
AG_BLE_CMD_STOP = 'stop'
AG_BLE_CMD_RUN = 'run'
AG_BLE_CMD_RWS = 'rws'
AG_BLE_CMD_CRC = 'crc_file'
AG_BLE_CMD_SWS = 'sws'
AG_BLE_CMD_GET_FILE = 'get_file'
AG_BLE_CMD_DWG_FILE = 'dwg_file'
AG_BLE_CMD_QUERY = 'n2lh_query'
AG_BLE_CMD_SCAN = 'scan'
AG_BLE_CMD_SCAN_LI = 'scan_li'
AG_BLE_ANS_DIR_EMPTY = 'empty -1'
AG_BLE_CMD_RLI = 'rli'
AG_BLE_CMD_RHS = 'rhs'
AG_BLE_CMD_FORMAT = 'format'
AG_BLE_CMD_LED = 'leds'
AG_BLE_CMD_EBR = 'ebr'
AG_BLE_CMD_MBL = 'mbl'
AG_BLE_CMD_LOG_TOGGLE = 'log'
AG_BLE_CMD_GSR = 'gsr'
AG_BLE_CMD_WLI = 'wli'
AG_BLE_CMD_WHS = 'whs'
AG_BLE_CMD_GSR_DO = 'gsr_do'
AG_BLE_CMD_RESET = 'reset'
AG_BLE_CMD_UPTIME = 'uptime'
AG_BLE_CMD_CFS = 'free_space'
AG_BLE_CMD_RFN = 'rfn'
AG_BLE_CMD_MTS = 'mts'
AG_BLE_CMD_WAK = 'wak'
AG_BLE_CMD_CONFIG = 'config'
AG_BLE_CMD_DEL_FILE = 'del_file'
AG_BLE_ANS_CONN_ALREADY = 'already connected'
AG_BLE_ANS_CONN_OK = 'connected'
AG_BLE_ANS_CONN_PROGRESS = 'connecting'
AG_BLE_ANS_CONN_ERR = 'connection fail'
AG_BLE_ANS_DISC_ALREADY = 'was not connected'
AG_BLE_ANS_DISC_OK = 'disconnected'
AG_BLE_EMPTY = 'not init'
AG_BLE_END_THREAD = 'ble_bye'
AG_BLE_ANS_GET_FILE_OK = 'got file ok!'
AG_BLE_ANS_GET_FILE_ERR = 'got file error'
AG_BLE_ANS_HCI_OK = 'HCI interface set OK'
AG_BLE_ANS_HCI_ERR = 'HCI interface set bad'


AG_N2LH_END_THREAD = 'n2lh_bye'
AG_N2LH_PATH_BASE = 'bas'
AG_N2LH_PATH_BLE = 'ble'
AG_N2LH_PATH_GPS = 'gps'
AG_N2LH_NOTIFICATION = 'ntf'


AG_N2LL_CMD_BYE = 'n2ll_bye'
AG_N2LL_CMD_WHO = 'n2ll_who'
AG_N2LL_CMD_QUERY = 'n2ll_query'
AG_N2LL_CMD_ROUTE = 'n2ll_route'
AG_N2LL_CMD_UNROUTE = 'n2ll_unroute'
AG_N2LL_CMD_BLED = 'n2ll_bled'
AG_N2LL_CMD_INSTALL_DDH = 'n2ll_install_ddh'
AG_N2LL_CMD_KILL_DDH = 'n2ll_uninstall_ddh'
AG_N2LL_CMD_VIEW_DDH = 'n2ll_view_ddh'
AG_N2LL_ANS_BYE = 'bye you by N2LL'
AG_N2LL_ANS_ROUTE_OK_FULL = 'ngrok routed in mac {} port {} url {}'
AG_N2LL_ANS_ROUTE_OK = 'ngrok routed in mac {}'
AG_N2LL_ANS_ROUTE_NOK = 'ngrok not routed in mac {}'
AG_N2LL_ANS_ROUTE_ERR_PERMISSIONS = 'error: few permissions to rm ngrok'
AG_N2LL_ANS_ROUTE_ERR_ALREADY = 'error: ngrok not grep at {}, maybe runs somewhere else?'
AG_N2LL_ANS_NOT_FOR_US = 'cmd not for us'


AG_GPS_OK = 'AG_GPS_OK:'
AG_GPS_ERROR = 'AG_GPS_ERROR:'
AG_GPS_EXCEPTION = 'AG_GPS_EXCEPTION:'


AG_SMS_OK = 'AG_SMS_OK:'
AG_SMS_ERROR = 'AG_SMS_ERROR:'
AG_SMS_EXCEPTION = 'AG_SMS_EXCEPTION:'


AG_DUMMY_OK = 'AG_DUMMY_OK:'
AG_DUMMY_ERROR = 'AG_DUMMY_ERROR:'
AG_DUMMY_EXCEPTION = 'AG_DUMMY_EXCEPTION:'


def get_ngrok_bin_name() -> str:
    _s = os.uname().nodename
    _m = os.uname().machine
    if _m == 'armv7l':
        return 'ngrok_rpi'
    if _s == 'rasberrypi' or _s == 'rpi':
        return 'ngrok_rpi'
    return 'ngrok'


def check_ngrok_can_be_run():
    name = get_ngrok_bin_name()
    cmd = '{} -h'.format(name)
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        print('{} found'.format(name))
        return True
    print('maybe you need to move ngrok to /usr/bin ?')
    if linux_is_rpi():
        print('also, maybe you meant ngrok_rpi ?')


def create_empty_crontab_file_for_ddh():
    """ empties and create a new system-wide crontab file """
    ct = CronTab(user='root')
    ct.write('/etc/crontab')


def create_populated_crontab_file_for_ddh():
    """ writes new populated system-wide crontab file """
    ct = CronTab(user='root')
    job = ct.new(command='/home/pi/li/ddh/ddh_run.sh', comment='launch DDH')
    job.minute.every(2)
    ct.write('/etc/crontab')


def does_cron_job_exists_by_comment(file_name: str, comm: str):
    """ checks if job w/ comment exists in crontab file 'f' """
    assert file_name
    ct = CronTab(user='root', tabfile=file_name)
    iter_job = ct.find_comment(comm)
    rv = len(list(iter_job))
    s = 'job w/ comment {} present at file {}? {} '
    print(s.format(comm, file_name, bool(rv)))
    return bool(rv)

