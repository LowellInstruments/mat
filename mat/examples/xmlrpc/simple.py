import os
import queue
from mat.ble_xmlrpc_client import XS_BLE_CMD_CONNECT, XS_BLE_CMD_STS, XS_BLE_BYE, XS_BLE_EXC_LC, XS_BLE_EXC_XS
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY, MAC_DO2_0
from mat.examples.xmlrpc._common import xr_launch_threads


address = MAC_DO2_0


def simple(xs_ble_cmd, dummy=False):
    q_cmd = queue.Queue()
    q_ans = queue.Queue()
    xr_launch_threads(q_cmd, q_ans)
    mac = MAC_DO2_0_DUMMY if dummy else address

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
