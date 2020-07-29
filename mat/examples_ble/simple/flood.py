import bluepy.btle as ble

from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble import _macs
import time
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['lp2']


def attack():
    try:
        with LoggerControllerBLE(mac, hci_if=0) as lc:
            lc.flood(100)
            time.sleep(6)

            # next command will contain whatever number of flooding
            # command answers the logger could manage + its own answer
            lc.get_time()
            time.sleep(1)
            rv = lc.get_time()
            print(rv)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def simple():
    try:
        with LoggerControllerBLE(mac, hci_if=0) as lc:
            # rv = lc.get_time()
            # print('\t{}'.format(rv))
            rv = lc.command(STATUS_CMD)
            print('\tSTS --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: flood')
    attack()
    # simple()
    print('APP: done')
