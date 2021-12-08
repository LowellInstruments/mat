import math
import time
from mat.ble_utils_shared import xmd_frame_check_crc


SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'
NAK = b'\x15'


def _debug(s, verbose):
    if verbose:
        print(s)


def rn4020_xmodem_get_file(lc, file_size, p=None, verbose=False):
    file_built = bytes()
    _rt = 0
    _len = 0

    # enable debug
    verbose = True

    # send C character
    _debug('<- C', verbose)
    lc.ble_write(b'C')

    while 1:
        # start anew at every frame
        lc.dlg.buf = bytes()
        if _rt == 3:
            _debug('<- can _rt 3', verbose)
            _can(lc)
            # give remote logger time to reset XMODEM
            time.sleep(5)
            return bytes()

        _bef = time.perf_counter()
        # wait for one second as maximum
        if not lc.per.waitForNotifications(1):
            # timeout control byte
            _debug('-> timeout rx control byte', verbose)
            _nak(lc)
            _rt += 1
            continue

        # control byte arrived in < 1 sec, check it
        _in_b = bytes([lc.dlg.buf[0]])
        if _in_b == EOT:
            _debug('-> eot', verbose)
            _ack(lc)
            return file_built
        if _in_b == SOH:
            # print('-> soh')
            _len = 128 + 5
        elif _in_b == STX:
            # print('-> stx')
            _len = 1024 + 5
        elif _in_b == CAN:
            # canceled by remote
            e = '-> can ctrl {}'.format(_in_b)
            _debug(e, verbose)
            _ack(lc)
            return bytes()
        else:
            # weird control byte arrived
            _rt += 1
            _nak(lc)
            continue

        # rx rest of frame
        _now = time.perf_counter()
        _rem = 1 - (_now - _bef)
        _till = _now + _rem
        timeout = False
        while 1:
            lc.per.waitForNotifications(0.1)
            if time.perf_counter() > _till:
                timeout = True
                break
            if len(lc.dlg.buf) == _len:
                break
        if timeout:
            # timeout rest of frame
            _rt += 1
            _debug('-> timeout rx frame', verbose)
            _nak(lc)
            continue

        # PARSE DATA ok
        if xmd_frame_check_crc(lc.dlg.buf):
            file_built += lc.dlg.buf[3:_len - 2]
            lc.dlg.buf = lc.dlg.buf[_len:]
            _ack(lc)
            _rt = 0
            # notify GUI, if any
            if p:
                f = open(p, 'w+')
                _ = len(file_built) / file_size * 100
                _ = _ if _ < 100 else 100
                f.write(str(math.ceil(_)))
                f.close()
        else:
            # PARSE DATA not OK, yes retries left
            _debug('<- crc NAK', verbose)
            _rt += 1
            _nak(lc)


def _ack(lc):
    lc.ble_write(ACK)


def _nak(lc):
    lc.ble_write(NAK)


def _can(lc):
    lc.ble_write(CAN)
    lc.ble_write(CAN)
    lc.ble_write(CAN)


class XModemException(Exception):
    pass
