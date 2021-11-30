import os
import queue

from mat.ble.xmlrpc_beta.examples._common import xr_launch_threads
from mat.ble.xmlrpc_beta.xmlrpc_lc_ble_client import *


def simple(xs_ble_cmd, dummy=False):
    q_cmd = queue.Queue()
    q_ans = queue.Queue()
    xr_launch_threads(q_cmd, q_ans)
    mac = '11:22:33:44:55:66'

    # connect
    q_cmd.put((XS_BLE_CMD_CONNECT, mac, 0))
    a = q_ans.get()
    print('\tEXAMPLE -> {}'.format(a))

    # whatever command
    q_cmd.put((xs_ble_cmd, ))
    a = q_ans.get()
    if a == XS_BLE_EXC_LC:
        print('(xs) ! (from lc) {}, quitting'.format(a))
        os._exit(1)
    if a == XS_BLE_EXC_XS:
        print('(xs) ! (from xs) {}, quitting'.format(a))
        os._exit(1)
    print('\tEXAMPLE -> {}'.format(a))

    # disconnect + bye
    q_cmd.put((XS_BLE_BYE, ))
    a = q_ans.get()
    print('\tEXAMPLE -> {}'.format(a))


if __name__ == '__main__':
    simple(XS_BLE_CMD_STS)
