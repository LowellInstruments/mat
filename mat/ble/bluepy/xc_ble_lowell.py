import os
import threading
import time
import xmlrpc
from http.client import RemoteDisconnected


XS_DEFAULT_PORT = 9000
XS_PID_FILE = '/dev/shm/pid_xr'
XS_BREAK = 'break'
XS_BLE_BYE = 'xs_ble_bye'
XS_BLE_EXC_LC = 'xs_ble_exc_lc'
XS_BLE_EXC_XS = 'xs_ble_exc_xs'

XS_BLE_CMD_SCAN = 'xs_ble_cmd_scan'
XS_BLE_CMD_SCAN_DUMMY = 'xs_ble_cmd_scan_dummy'
XS_BLE_CMD_DISCONNECT = 'xs_ble_cmd_disconnect'
XS_BLE_CMD_DISCONNECT_FOR_SURE = 'xs_ble_cmd_disconnect_for_sure'
XS_BLE_CMD_STATUS_N_DISCONNECT = 'xs_ble_cmd_status_n_disconnect'
XS_BLE_CMD_CONNECT = 'xs_ble_cmd_connect'
XS_BLE_CMD_DIR = 'xs_ble_cmd_dir'
XS_BLE_CMD_RFN = 'xs_ble_cmd_rfn'
XS_BLE_CMD_DWG = 'xs_ble_cmd_dwg'
XS_BLE_CMD_DWL = 'xs_ble_cmd_dwl'
XS_BLE_CMD_STS = 'xs_ble_cmd_sts'
XS_BLE_CMD_GFV = 'xs_ble_cmd_gfv'
XS_BLE_CMD_RLI = 'xs_ble_cmd_rli'
XS_BLE_CMD_GTM = 'xs_ble_cmd_gtm'
XS_BLE_CMD_STM = 'xs_ble_cmd_stm'
XS_BLE_CMD_UTM = 'xs_ble_cmd_utm'
XS_BLE_CMD_LED = 'xs_ble_cmd_led'
XS_BLE_CMD_WAK = 'xs_ble_cmd_wak'
XS_BLE_CMD_EBR = 'xs_ble_cmd_ebr'
XS_BLE_CMD_LOG = 'xs_ble_cmd_log'
XS_BLE_CMD_CFS = 'xs_ble_cmd_cfs'
XS_BLE_CMD_RHS = 'xs_ble_cmd_rhs'
XS_BLE_CMD_WLI = 'xs_ble_cmd_wli'
XS_BLE_CMD_WHS = 'xs_ble_cmd_whs'
XS_BLE_CMD_FRM = 'xs_ble_cmd_frm'
XS_BLE_CMD_MTS = 'xs_ble_cmd_mts'
XS_BLE_CMD_RST = 'xs_ble_cmd_rst'
XS_BLE_CMD_GDO = 'xs_ble_cmd_gdo'
XS_BLE_CMD_DEL = 'xs_ble_cmd_del'
XS_BLE_CMD_TST = 'xs_ble_cmd_tst'
XS_BLE_CMD_RUN = 'xs_ble_cmd_run'
XS_BLE_CMD_STP = 'xs_ble_cmd_stp'
XS_BLE_CMD_RWS = 'xs_ble_cmd_rws'
XS_BLE_CMD_SWS = 'xs_ble_cmd_sws'
XS_BLE_CMD_CFG = 'xs_ble_cmd_cfg'


def xr_assert_api_or_die(s, api: list):
    if s in api:
        return

    valid = [s for s in api if s.startswith('xs_ble_')]
    print('error {} -> not part of our BLE XS API'.format(s))
    for s in valid:
        print('\t - {}'.format(s))
    os._exit(1)


def xc_run(url, q_cmd_in, q_ans_out=None):

    # url: 'http://localhost:<port>'
    xc = xmlrpc.client.ServerProxy(url, allow_none=True)
    print('th_xc: started at url {}'.format(url))

    while 1:

        # prevents CPU hog
        time.sleep(.1)

        while not q_cmd_in.empty():
            # c: ('scan', 0, 'all')
            c = q_cmd_in.get()

            # ends client loop, useful to re-orient url
            if c[0] == XS_BREAK:
                return 'XR client restarted'

            # remote function call + collect answer
            try:
                a = xc.xs_client_entry_point(c)
                if q_ans_out:
                    q_ans_out.put(a)

            except (xmlrpc.client.Fault, RemoteDisconnected) as ex:
                print('XR cli exc -> {}'.format(ex))
