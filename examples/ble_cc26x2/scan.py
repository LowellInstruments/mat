from bluepy.btle import Scanner

from mat.logger_controller_ble import FAKE_MAC_CC26X2


def get_ordered_scan_results(dummies=False) -> dict:
    """
    Does a BLE scan and returns friendly results lists
    :param dummies: add a couple dummies for resting
    :return: near and far lists
    """

    till = 3
    s = 'detecting nearby loggers, please wait {} seconds...'
    print(s.format(till))
    sr = Scanner().scan(float(till))

    # bluepy 'scan results (sr)' format -> friendlier one
    sr_f = {each_sr.addr: each_sr.rssi for each_sr in sr}

    if dummies:
        sr_f[FAKE_MAC_CC26X2] = -10
        sr_f['dummy_2'] = -20

    # nearest: the highest value, less negative
    sr_f_near = sorted(sr_f.items(), key=lambda x: x[1], reverse=True)
    sr_f_far = sorted(sr_f.items(), key=lambda x: x[1], reverse=False)
    return sr_f_near, sr_f_far


if __name__ == '__main__':
    _near, _far = get_ordered_scan_results(dummies=True)
    print('scan results: nearest-first')
    print(_near)
    print('scan results: farthest-first')
    print(_far)
