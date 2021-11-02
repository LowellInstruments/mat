import time
from mat import gps


# for hardware devices, this real test complements
# work that can be done with py.test
# test this with both GPS plugged and unplugged
if __name__ == '__main__':
    USB_PORT = '/dev/ttyUSB0'
    BAD_USB_PORT = '/dev/ttyUSBX'

    g = gps.GPS(USB_PORT, 4800)
    a = time.perf_counter()
    s = g.get_gps_info(timeout=1)
    b = time.perf_counter()
    t = b - a
    print('took {:.1f} seconds, rv = {}'.format(t, s))
    assert (b - a <= 1.1)
    a = time.perf_counter()
    s = g.get_gps_info(timeout=3)
    b = time.perf_counter()
    t = b - a
    print('took {:.1f} seconds, rv = {}'.format(t, s))
    assert (b - a <= 3.1)
    del g

    # forcing and controlling an error
    g = gps.GPS(BAD_USB_PORT, 4800)
    if not g.port:
        e = 'usb error port name{}'
        print(e.format(BAD_USB_PORT))

    # done
    print('real GPS test done')
