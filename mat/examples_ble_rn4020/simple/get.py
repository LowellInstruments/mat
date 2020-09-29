import time
import bluepy.btle as ble
from mat.data_converter import default_parameters, DataConverter
from mat.examples_ble_rn4020.simple.dir import ls_lid_rn4020
from mat.examples_ble_rn4020.simple.xmodem_ble_rn4020 import xmd_get_file_rn4020
from mat.utils import print_colors as p_c
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_rn4020._macs import mac_def


# use default MAC or override it
mac = mac_def


def _convert_file(data, path, n):
    if data == b'':
        return False

    try:
        with open(path, 'wb') as f:
            f.write(data)
            f.truncate(n)
        pars = default_parameters()
        converter = DataConverter(path, pars)
        converter.convert()
        print('converted file {} ok'.format(path))
    except Exception as ex:
        print(ex)
        return False
    return True


def ls_dl(f_name, f_size):
    rv = False
    el = None
    f_data = None

    try:
        with LoggerControllerBLE(mac) as lc:
            # set RN4020 fast mode
            _ = lc.send_btc()
            if not _:
                print('\tcould not BTC, leaving')
                return False
            print('\tBTC -> {}'.format(_))

            # GET cmd done by us not command(), purge first
            lc.dlg.clr_buf()
            g = 'GET {:02x}{}\r'
            cmd = g.format(len(f_name), f_name)
            lc.ble_write(cmd.encode())
            _till = time.time() + 10
            while time.time() < _till:
                lc.per.waitForNotifications(.1)
                if time.time() >= _till:
                    print('\terror GET')
                    return False

                # it is going well
                _ = lc.dlg.buf.decode().strip()
                if _ == 'GET 00':
                    lc.dlg.set_file_mode(True)
                    el = time.perf_counter()
                    s = '\tDownloading {}, {} bytes...'
                    print(s.format(f_name, f_size))
                    rv, f_data = xmd_get_file_rn4020(lc)
                    break

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))

    finally:
        lc.dlg.set_file_mode(False)
        if rv:
            el = time.perf_counter() - el
            s = '\t--> data rate {} bytes / sec'
            print(p_c.OKGREEN + s.format(int(f_size / el)) + p_c.ENDC)
            return _convert_file(f_data, f_name, f_size)
        return False


if __name__ == '__main__':
    ls = ls_lid_rn4020()

    # name = ls[0].decode()
    # size = int(ls[1].decode())
    # files in logger_tp
    # name, size = '18106C9_MATP_(2).lid', 856944
    name, size = '18106C9_MATP_(4).lid', 33024
    # files in MAT_0
    # name, size = '17042DF_T&P_(0).lid',   371161

    how_many = 1
    good_ones = 0
    for i in range(how_many):
        if ls_dl(name, size):
            good_ones += 1
        time.sleep(5)
    print('{}/{}'.format(good_ones, how_many))
