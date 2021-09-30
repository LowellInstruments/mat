import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE, GET_SENSOR_READING_DO, LED_CMD
from mat.logger_controller import FIRMWARE_VERSION_CMD, STATUS_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


def led():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(LED_CMD)
            print('\t\tLED --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    led()
