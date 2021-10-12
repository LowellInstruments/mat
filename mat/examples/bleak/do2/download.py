import pathlib
import time
from mat.bleak.ble_logger_do2 import BLELoggerDO2
from mat.bleak.ble_logger_do2_dummy import BLELoggerDO2Dummy
from mat.examples.bleak.do2.convert import cnv
from mat.examples.bleak.do2.macs import mac


def download(file_name, file_size, dummy=False):
    lc_class = BLELoggerDO2Dummy if dummy else BLELoggerDO2
    lc = lc_class()
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

