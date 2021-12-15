from mat.crc import calculate_local_file_crc
from mat.data_converter import default_parameters, DataConverter
from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R
from mat.ble.bluepy.examples.examples_utils import get_mac
from pathlib import Path


def file_convert(path):
    try:
        assert path.endswith('.lid')
        print('\t\tConverting: {} --> '.format(path), end='')
        parameters = default_parameters()
        converter = DataConverter(path, parameters)
        converter.convert()
        return True
    except Exception as ex:
        print(ex)


def file_dwg(file_name, file_size: int, cla=LoggerControllerCC26X2R):

    mac = get_mac(cla)
    lc = cla(mac)

    if not lc.open():
        print('{} connection error'.format(__name__))
        return

    rv = lc.ble_cmd_stp()
    print('STOP {}'.format(rv))

    rv = lc.ble_cmd_slw_ensure('OFF')
    print('SLW is {}'.format(rv))

    rv = lc.ble_cmd_dwg(file_name)
    print('DWG {}'.format(rv))

    rv = lc.ble_cmd_dwl(file_size)
    path = str(Path.home() / 'Downloads' / file_name)

    if not rv:
        print('DWL error')

    else:
        with open(path, 'wb') as f:
            f.write(rv)
            print('file downloaded to {}'.format(path))
        local_crc = calculate_local_file_crc(path)

        remote_crc = lc.ble_cmd_crc(file_name)
        rv = local_crc.lower() == remote_crc
        print('CRC check == {}'.format(rv))

        rv = file_convert(path)
        print('conversion == {}'.format(rv))
        if not rv:
            print('OK if dummy file')

    lc.close()


if __name__ == '__main__':
    file_dwg('50.lid', 102400)
