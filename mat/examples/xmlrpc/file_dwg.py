import queue

from mat.ble_xmlrpc_client import XS_BLE_CMD_CONNECT, XS_BLE_CMD_STP, XS_BLE_CMD_DWG, XS_BLE_CMD_DWL
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY, MAC_DO2_0
from mat.examples.xmlrpc._common import xr_launch_threads


address = MAC_DO2_0


def dwg_file(s, n, dummy=False):
    q_cmd = queue.Queue()
    q_ans = queue.Queue()
    xr_launch_threads(q_cmd, q_ans)

    mac = MAC_DO2_0_DUMMY if dummy else address

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
