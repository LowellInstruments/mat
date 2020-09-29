import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
import time
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


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


if __name__ == '__main__':
    print('APP: flood')
    attack()
    print('APP: done')
