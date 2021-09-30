from mat.data_converter import default_parameters, DataConverter
from mat.bluepy.logger_controller_ble_do import LoggerControllerBLEDO
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12


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


def example_file_dwg(file_name, file_size: int):
    lc = LoggerControllerBLEDO(mac)
    if lc.open():
        rv = lc.ble_cmd_stp()
        print('STOP {}'.format(rv))

        rv = lc.ble_cmd_slw_ensure('OFF')
        print('SLW is {}'.format(rv))

        rv = lc.ble_cmd_dwg(file_name, '.', file_size, None)
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
    example_file_dwg('MAT.cfg', 189)
