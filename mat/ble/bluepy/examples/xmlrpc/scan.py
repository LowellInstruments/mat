import queue

from mat.ble.bluepy.examples.xmlrpc._common import xr_launch_threads
from mat.ble.bluepy.xc_ble_lowell import *


def scan(dummy=False):
    q_cmd = queue.Queue()
    q_ans = queue.Queue()
    xr_launch_threads(q_cmd, q_ans)

    c = XS_BLE_CMD_SCAN
    if dummy:
        c = XS_BLE_CMD_SCAN_DUMMY
    q_cmd.put((c, 0, 3.0))
    a = q_ans.get()
    print('\tEXAMPLE -> {}'.format(a))

    q_cmd.put((XS_BLE_BYE,))
    a = q_ans.get()
    print('\tEXAMPLE -> {}'.format(a))


if __name__ == '__main__':
    scan()
