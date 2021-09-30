from mat.ble_xmlrpc_client import XS_BLE_CMD_GTM
from mat.examples.xmlrpc.simple import simple


def get_time(dummy=False):
    simple(XS_BLE_CMD_GTM, dummy)


if __name__ == '__main__':
    get_time()
