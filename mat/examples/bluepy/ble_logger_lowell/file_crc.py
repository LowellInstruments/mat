from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.macs import get_mac


def file_crc(s: str, cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_crc(s)
        print('file remote crc: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    # 1E8C58BC file contents '1234567890 abcdef!!"
    # aeef2a50 file contents 'abcdefgh'
    file_crc('MAT.cfg')
