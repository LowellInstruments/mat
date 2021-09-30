from mat.bluepy.ble_xmlrpc_client import XS_BLE_EXC_LC
from mat.examples.bleak.do2.macs import MAC_DO2_0
from mat.examples.xmlrpc.simple import simple


address = MAC_DO2_0


def exc_lc(dummy=False):
    simple(XS_BLE_EXC_LC, dummy)


if __name__ == '__main__':
    exc_lc()
