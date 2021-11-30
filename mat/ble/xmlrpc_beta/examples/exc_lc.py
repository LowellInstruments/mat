from mat.ble.xmlrpc_beta.examples.simple import simple
from mat.ble.xmlrpc_beta.xmlrpc_lc_ble_client import XS_BLE_EXC_LC


def exc_lc(dummy=False):
    simple(XS_BLE_EXC_LC, dummy)


if __name__ == '__main__':
    exc_lc()
