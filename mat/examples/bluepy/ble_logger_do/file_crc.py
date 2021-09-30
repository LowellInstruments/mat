from mat.bluepy.logger_controller_ble_do import LoggerControllerBLEDO
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12


def example_file_remote_crc(file_name: str):
    lc = LoggerControllerBLEDO(mac)
    if lc.open():
        rv = lc.ble_cmd_crc(file_name)
        print('file remote crc: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    # 1E8C58BC file contents '1234567890 abcdef!!"
    # aeef2a50 file contents 'abcdefgh'
    example_file_remote_crc('MAT.cfg')
