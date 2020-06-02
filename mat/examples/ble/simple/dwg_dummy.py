import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple import _macs

# mac = _macs.puz
mac = _macs.sxt050


def dwg_dummy():
    try:
        with LoggerControllerBLE(mac) as lc:
            name = 'dummy.lid'
            size = 4096
            print('\tDownloading {}...', name)
            rv = lc.command('DWG', name)
            print(rv)
            # lc.dwl_chunk(0)
            lc.dwl_chunk(1)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    dwg_dummy()

