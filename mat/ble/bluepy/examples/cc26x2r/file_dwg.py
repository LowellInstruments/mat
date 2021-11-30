from mat.data_converter import default_parameters, DataConverter
from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R
from mat.ble.bluepy.examples.examples_utils import get_mac


def file_convert(path):
    try:
        assert path.endswith('.lid')
        print('\t\tConverting: {} --> '.format(path), end='')
        parameters = default_parameters()
        converter = DataConverter(path, parameters)
        converter.convert()
        print('conversion ok')
    except Exception as ex:
        print('conversion error')
        print(ex)


def file_dwg(file_name, file_size: int, cla=LoggerControllerCC26X2R):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_stp()
        print('STOP {}'.format(rv))

        rv = lc.ble_cmd_slw_ensure('OFF')
        print('SLW is {}'.format(rv))

        rv = lc.ble_cmd_dwg(file_name)
        print('DWG {}'.format(rv))

        rv = lc.ble_cmd_dwl(file_size)
        if rv:
            with open('a.lid', 'wb') as f:
                f.write(rv)
            file_convert('a.lid')
        else:
            print('DWL error')

    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    file_dwg('MAT.cfg', 189)
