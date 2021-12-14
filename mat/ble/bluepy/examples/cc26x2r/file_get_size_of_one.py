from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R
from mat.ble.bluepy.examples.examples_utils import get_mac


def file_size(s: str, cla=LoggerControllerCC26X2R):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_siz(s)
        print('> get one file size: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    f = 'dummy_23.lid'
    file_size(f)