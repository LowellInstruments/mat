from mat.ble.bluepy.examples.xmlrpc.simple import simple
from mat.ble.bluepy.xc_ble_lowell import XS_BLE_EXC_LC


def exc_lc(dummy=False):
    simple(XS_BLE_EXC_LC, dummy)


if __name__ == '__main__':
    exc_lc()
