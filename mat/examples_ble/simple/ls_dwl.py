import time
import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from pprint import pprint
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['lp2']


# usually, this creates a big file for testing
def mts():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command('STP')
            print('\tSTP --> {}'.format(result))

            pairs = lc_ble.ls_lid()
            print('\tDIR -->')
            pprint(pairs)

            # result = lc_ble.command('MTS')
            # print('\tMTS --> {}'.format(result))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def dwl():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command('STP')
            print('\tSTP --> {}'.format(result))

            # pairs = lc_ble.ls_lid()
            # print('\tDIR -->')
            # pprint(pairs)
            # return

            # result = lc_ble.command('DWG', 'dummy.lid')
            result = lc_ble.command('DWG', '2002001_sxt_(2).lid')
            print('\tDWG --> {}'.format(result))

            a = time.perf_counter()
            # ~ 10 KB / s
            for i in range(100):
                lc_ble.dwl_chunk(0)
            b = time.perf_counter()
            print(b - a)


            # for name, size in pairs.items():
            #     result = lc_ble.command('DWG', name)
            #     print('\tDWG --> {}'.format(result))
            #
            #     for i in range(3):
            #         result = lc_ble.command('DWL', str(i))
            #         print('\tDWL --> {}'.format(result))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    dwl()
    # mts()

