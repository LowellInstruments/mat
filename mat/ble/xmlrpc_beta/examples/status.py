from mat.ble.xmlrpc_beta.examples.simple import simple
from mat.ble.xmlrpc_beta.xmlrpc_lc_ble_client import XS_BLE_CMD_STS


def status(dummy=False):
    simple(XS_BLE_CMD_STS, dummy)


if __name__ == '__main__':
    status()
