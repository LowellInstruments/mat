import time
import bluepy


def connect_rn4020(lc):
    # crashes when non-root
    # assert ble_linux_write_parameters_as_fast(lc.h)

    uuid_s = '00035b03-58e6-07dd-021a-08123a000300'
    uuid_c = '00035b03-58e6-07dd-021a-08123a000301'

    try:
        lc.per = bluepy.btle.Peripheral(lc.mac, iface=lc.url_hh, timeout=10)
        lc.per.setDelegate(lc.dlg)
        lc.svc = lc.per.getServiceByUUID(uuid_s)
        lc.cha = lc.svc.getCharacteristics(uuid_c)[0]
        desc = lc.cha.valHandle + 1
        lc.per.writeCharacteristic(desc, b'\x01\x00')
        # do not remove, damn Jim!
        time.sleep(1.5)
        return True

    except (AttributeError, bluepy.btle.BTLEException) as ex:
        return False


def utils_logger_is_rn4020(mac, info: str):
    if mac.startswith('00:1e:c0'):
        return True

    if 'MATP-2W' in info:
        return True
