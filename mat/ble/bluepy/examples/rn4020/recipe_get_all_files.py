import time
import bluepy.btle as ble
from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020
from mat.data_converter import default_parameters, DataConverter
from mat.utils import PrintColors as PC
from pathlib import Path


def _g(_s):
    print('{}{}{}'.format(PC.OKGREEN, _s, PC.ENDC))


def _b(_s):
    print('{}{}{}'.format(PC.OKBLUE, _s, PC.ENDC))


def _r(_s):
    print('{}{}{}'.format(PC.FAIL, _s, PC.ENDC))


def _convert_file(data, path, _size):
    if data == b'':
        return False

    with open(path, 'wb') as f:
        f.write(data)
        f.truncate(_size)
    pars = default_parameters()
    converter = DataConverter(path, pars)
    converter.convert()
    print('converted {} OK'.format(path))
    return True


def _get_n_convert(lc, f_name, f_size):

    el = time.perf_counter()
    print('getting {}, {} bytes'.format(f_name, f_size))
    data = lc.ble_cmd_get(f_name, f_size)
    if not data:
        _r('error downloading {}'.format(f_name))
        return

    el = time.perf_counter() - el
    s = 'data rate {} bytes / sec'
    _g(s.format(int(f_size / el)))
    path = str(Path.home() / 'Downloads' / f_name)
    _convert_file(data, path, f_size)


def recipe_get_all_files():

    # ---------------------------------------------
    # feel free to call this to see any BLE around
    # devs = ble_scan_for_loggers(0, 5.0)
    # ---------------------------------------------

    # -------------------------
    # set mac to be downloaded
    # -------------------------
    mac = '00:1E:C0:3D:7A:F2'
    lc = LoggerControllerRN4020(mac)

    if not lc.open():
        print('error open')
        return
    print('logger connected OK')

    if not lc.ble_cmd_stp():
        lc.close()
        print('error STP')
        return
    print('logger stopped OK')

    if not lc.ble_cmd_stm():
        lc.close()
        print('error STM')
    print('logger sync-timed OK')

    file_list = lc.ble_cmd_dir_ext('.lid')
    print('files in logger {}'.format(file_list))

    for name, size in file_list.items():
        _get_n_convert(lc, name, size)
        time.sleep(2)

    lc.close()
    print('logger closed OK')


if __name__ == '__main__':
    try:
        recipe_get_all_files()

    except ble.BTLEException as ble_ex:
        print(ble_ex)
    except AttributeError as ae:
        print(ae)

