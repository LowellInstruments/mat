import subprocess as sp
from packaging import version
import platform
from mat.data_converter import default_parameters, DataConverter


def check_bluez_version():
    # cannot check bluez on non-linux platforms
    if not platform.system() in ('Linux', 'linux'):
        return True

    # old bluez give 'write not permitted' errors
    # when working with RN4020 loggers
    s = 'bluetoothctl -v'
    rv = sp.run(s, shell=True, stdout=sp.PIPE)
    v = rv.stdout.decode()
    v = v.replace('bluetoothctl: ', '')
    v = v.replace('\n', '')
    return version.parse(v) >= version.parse('5.61')


def crc16(data):
    crc = 0x0000
    length = len(data)
    for i in range(0, length):
        crc ^= data[i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    v = crc & 0xFFFF
    return v.to_bytes(2, 'big')


def xmd_frame_check_crc(b):
    rx_crc = b[-2:]
    data = b[3:-2]
    calc_crc = crc16(data)
    print(rx_crc, calc_crc)
    return calc_crc == rx_crc


def utils_mat_convert_data(data, path, size):
    if data == b'':
        return False
    try:
        with open(path, 'wb') as f:
            f.write(data)
            f.truncate(size)
        pars = default_parameters()
        converter = DataConverter(path, pars)
        converter.convert()
        return True
    except Exception as ex:
        print(ex)
        return False


