import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple._macs import mac


def signal_strength(a=mac):
    try:
        while 1:
            for d in ble.Scanner().scan(1):
                if d.addr == a:
                    print('\t{}   ->   {} dBm'.format(d.addr, d.rssi))
    except ble.BTLEException as ex:
        print(ex)


def scan():
    loggers = []
    try:
        for d in ble.Scanner().scan(3):
            print('\t{} ({}) {} dBm'.format(d.addr, d.addrType, d.rssi))
            loggers.append(d.addr)
    except ble.BTLEException as ex:
        print(ex)
    finally:
        return loggers


def list_characteristics(a=mac):
    try:
        with LoggerControllerBLE(a) as lc_ble:
            # connect, show characteristics' banner and info
            characteristics_list = lc_ble.per.getCharacteristics()
            print("Handle{}UUID{}Properties".format(' ' * 4, ' ' * 35))
            print("{}".format('-' * 60))
            for each in characteristics_list:
                text = "  0x{:02x}    {}   {}"
                print(text.format(each.getHandle(), str(each.uuid),
                                  each.propertiesToString()))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def list_services(a=mac):
    try:
        # connect, show services' banner and info
        with LoggerControllerBLE(a) as lc_ble:
            services_list = lc_ble.per.getServices()
            for each_service in services_list:
                print(each_service)
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    # signal_strength()
    scan()
    # list_services()
    # list_characteristics()
    print('APP: done')
