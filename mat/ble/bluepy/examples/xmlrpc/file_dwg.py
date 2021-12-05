import queue

from mat.ble.bluepy.examples.xmlrpc._common import xr_launch_threads
from mat.ble.bluepy.xc_ble_lowell import *


def dwg_file(mac, s, n, dummy=False):
    q_cmd = queue.Queue()
    q_ans = queue.Queue()
    xr_launch_threads(q_cmd, q_ans)

    q_cmd.put((XS_BLE_CMD_CONNECT, mac, 0))
    a = q_ans.get()
    print(a)

    q_cmd.put((XS_BLE_CMD_STP, ))
    a = q_ans.get()
    print(a)

    q_cmd.put((XS_BLE_CMD_DWG, s, '.', n,))
    a = q_ans.get()
    print(a)

    q_cmd.put((XS_BLE_CMD_DWL, n, None,))
    a = q_ans.get()
    print('xs_dwl OK') if a else 'xs_dwl error'


if __name__ == '__main__':
    name = 'dummy_16.lid'
    size = 167936
    dwg_file(name, size)
