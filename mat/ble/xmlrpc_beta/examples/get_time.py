from mat.ble.xmlrpc_beta.examples.simple import simple
from mat.ble.xmlrpc_beta.xmlrpc_lc_ble_client import XS_BLE_CMD_GTM


def get_time(dummy=False):
    simple(XS_BLE_CMD_GTM, dummy)


if __name__ == '__main__':
    get_time()
