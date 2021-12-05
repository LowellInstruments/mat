from mat.ble.ble_macs import MAC_LOGGER_MAT1_0
from mat.ble.bluepy.examples.xmlrpc.simple import simple
from mat.ble.bluepy.xc_ble_lowell import XS_BLE_CMD_GTM


mac = MAC_LOGGER_MAT1_0


def get_time():
    simple(XS_BLE_CMD_GTM, mac)


if __name__ == '__main__':
    get_time()
