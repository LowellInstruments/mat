import pathlib
import time
from mat.bleak.ble_logger_do2 import BLELoggerDO2
from mat.examples.bleak.do2.convert import cnv
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY

address = '60:77:71:22:c8:18'


def download(file_name, file_size, dummy=False):
    lc = BLELoggerDO2(dummy)
    mac = MAC_DO2_0_DUMMY if dummy else address
    lc.ble_connect(mac)

    # maybe slow it down
    lc.ble_cmd_ensure_slw_on()

    # target file
    s = pathlib.Path.home() / 'Downloads' / file_name
    a = lc.ble_cmd_dwg(file_name)
    if a == b'ERR':
        print('nope download no file')
        return

    # download the file
    now = time.perf_counter()
    data = lc.ble_cmd_dwl(file_size)

    # show performance
    took = time.perf_counter() - now
    print('speed {} B / s'.format(int(file_size / took)))
    with open(s, 'wb') as f:
        f.write(data)

    # try to convert it in case of real file
    if not dummy:
        cnv(s)

    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    name = '2006671_kim_20210923_115655.lid'
    size = 7573
    download(name, size)

