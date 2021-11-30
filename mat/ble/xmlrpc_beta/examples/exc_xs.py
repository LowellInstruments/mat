from mat.ble.xmlrpc_beta.examples.simple import simple
from mat.ble.xmlrpc_beta.xmlrpc_lc_ble_client import XS_BLE_EXC_XS


def exc_xs(dummy=False):
    simple(XS_BLE_EXC_XS, dummy)


if __name__ == '__main__':
    exc_xs()
