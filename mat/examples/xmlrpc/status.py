from mat.ble_xmlrpc_client import XS_BLE_CMD_STS
from mat.examples.xmlrpc.simple import simple


def status(dummy=False):
    simple(XS_BLE_CMD_STS, dummy)


if __name__ == '__main__':
    status()
