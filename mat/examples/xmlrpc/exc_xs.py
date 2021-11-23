from mat.bluepy.xmlrpc_lc_ble_client import XS_BLE_EXC_XS
from mat.examples.bleak.do2.macs import MAC_DO2_0
from mat.examples.xmlrpc.simple import simple


address = MAC_DO2_0


def exc_xs(dummy=False):
    simple(XS_BLE_EXC_XS, dummy)


if __name__ == '__main__':
    exc_xs()
