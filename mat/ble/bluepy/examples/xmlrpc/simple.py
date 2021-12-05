import os
import queue
from mat.ble.bluepy.examples.xmlrpc._common import xr_launch_threads
from mat.ble.bluepy.xc_ble_lowell import XS_BLE_CMD_CONNECT, XS_BLE_BYE, XS_BLE_EXC_LC, XS_BLE_EXC_XS


def simple(c, mac):
    q_cmd = queue.Queue()
    q_ans = queue.Queue()
    xr_launch_threads(q_cmd, q_ans)

    # step 1 -> connect
    q_cmd.put((XS_BLE_CMD_CONNECT, mac, 0))
    print('<- connect', mac)
    a = q_ans.get()
    print('-> {}'.format(a))

    # step 2 -> whatever command
    print('<-', c)
    q_cmd.put((c,))
    a = q_ans.get()
    if a in (XS_BLE_EXC_LC, XS_BLE_EXC_XS):
        print('(xs) ! (from lc) {}, quitting'.format(a))
        os._exit(1)
    print('-> {}'.format(a))

    # step 3 -> disconnect + bye
    q_cmd.put((XS_BLE_BYE, ))
    print('<- bye')
    a = q_ans.get()
    print('-> {}'.format(a))
