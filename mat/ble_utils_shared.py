import subprocess as sp
from packaging import version
import platform
from mat.data_converter import default_parameters, DataConverter


def check_bluez_version():
    if not platform.system() in ('Linux', 'linux'):
        return True

    # RN4020 loggers gave 'write not permitted' errors
    s = 'bluetoothctl -v'
    v = sp.run(s, shell=True, stdout=sp.PIPE)
    v = v.stdout.decode()
    v = v.replace('bluetoothctl: ', '')
    v = v.replace('\n', '')
    # -------------------------------
    # error -> 5.47, 5.50, 5.56, 5.58
    # maybe -> 5.51
    # works -> 5.61
    # -------------------------------
    a = version.parse(v) == version.parse('5.61')
    assert a, 'careful with bleak & bluez versions!'


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
    # print(rx_crc, calc_crc)
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


