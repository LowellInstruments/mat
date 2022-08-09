import bluepy
import time
from bluepy.btle import ADDR_TYPE_RANDOM

from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R


MTU_SIZE = 247

cfg_do = {
    "DFN": "low",
    "TMP": 0, "PRS": 0,
    "DOS": 1, "DOP": 1, "DOT": "puta",
    "TRI": 10, "ORI": 10, "DRI": 10,
    "PRR": 1,
    "PRN": 1,
    "STM": "2022-08-02 14:29:00",
    "ETM": "2030-11-12 12:14:20",
    "LED": 1
}


class MyDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)
        self.buf = bytes()

    def handleNotification(self, c_handle, data):
        # print(data)
        self.buf += data
        print(self.buf)


def _connect_do3(lc):
    uuid_s = 'f000c0c0-0451-4000-b000-000000000000'
    uuid_c = 'f000c0c2-0451-4000-b000-000000000000'
    uuid_w = 'f000c0c1-0451-4000-b000-000000000000'

    try:
        lc.per = bluepy.btle.Peripheral(lc.mac, iface=lc.h, timeout=10)
        lc.per.setDelegate(MyDelegate)
        lc.svc = lc.per.getServiceByUUID(uuid_s)
        lc.cha = lc.svc.getCharacteristics(uuid_c)[0]
        desc = lc.cha.valHandle + 1
        lc.per.writeCharacteristic(desc, b'\x01\x00')
        lc.per.setMTU(MTU_SIZE)
        lc.cha = lc.svc.getCharacteristics(uuid_w)[0]
        return True

    except (AttributeError, bluepy.btle.BTLEException) as ex:
        print('[ BLE ] cannot connect -> {}'.format(ex))
        return False


class DO3(LoggerControllerCC26X2R):
    def open(self) -> bool:
        return _connect_do3(self)


if __name__ == '__main__':
    a = DO3('F4:60:77:83:2B:6C')

    a.open()
    time.sleep(1)
    rv = a.ble_cmd_cfg(cfg_do)
    print('> config cmd: {}'.format(rv))
    a.close()
