import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['lp2']


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

