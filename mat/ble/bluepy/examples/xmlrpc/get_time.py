from mat.ble.bluepy.examples.xmlrpc.simple import simple
from mat.ble.bluepy.xc_ble_lowell import XS_BLE_CMD_GTM


def get_time(dummy=False):
    simple(XS_BLE_CMD_GTM, dummy)


if __name__ == '__main__':
    get_time()
