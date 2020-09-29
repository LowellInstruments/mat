import time
import crc16


SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'
NAK = b'\x15'


def xmd_get_file_rn4020(lc, sig=None):
    file_built = bytes()
    _rt = 0
    _len = 0

    # send C character
    _purge(lc)
    # print('<- C')
    lc.ble_write(b'C')

    while 1:
        # rx control stage, very demanding
        _till = time.perf_counter() + 1
        while 1:
            if lc.per.waitForNotifications(1):
                break
            if time.perf_counter() >= _till:
                _can(lc)
                return False

        # rx data stage
        _till = time.perf_counter() + 1
        _timeout = False
        while 1:
            lc.per.waitForNotifications(.001)
            _in_b = bytes([lc.dlg.x_buf[0]])

            # check first byte of chunk
            if _in_b == EOT:
                # print('-> eot')
                _ack(lc)
                return True, file_built
            if _in_b == SOH:
                # print('-> soh')
                _len = 128 + 5
            elif _in_b == STX:
                # print('-> stx')
                _len = 1024 + 5
            elif _in_b == CAN:
                # canceled by remote,
                print('-> can ctrl {}'.format(_in_b))
                _ack(lc)
                return False
            else:
                _purge(lc)
                _nak(lc)
                continue

            # received whole chunk
            if len(lc.dlg.x_buf) >= _len:
                break

            # timeout receiving data
            if time.perf_counter() >= _till:
                _timeout = True
                break

        # timeout rx whole chunk
        if _timeout and _rt < 3:
            print('<- nak timeout')
            _timeout = False
            _nak(lc)
            _till = time.perf_counter() + 1
            continue

        # PARSE DATA ok
        if _frame_check_crc(lc):
            file_built += lc.dlg.x_buf[3:_len - 2]
            lc.dlg.x_buf = lc.dlg.x_buf[_len:]
            _ack(lc)
            _rt = 0
            # notify GUI, if any
            if sig:
                sig.emit()
            continue

        # PARSE DATA not OK, no retries left
        if _rt == 3:
            print('<- crc CAN')
            _can(lc)
            _purge(lc)
            return False

        # PARSE DATA not OK, yes retries left
        print('<- crc NAK')
        _rt += 1
        _purge(lc)
        _nak(lc)


def _purge(lc):
    _till = time.time() + 1
    while time.time() < _till:
        lc.per.waitForNotifications(0.01)
    lc.dlg.x_buf = bytes()


def _ack(lc):
    # print('<- ACK')
    lc.ble_write(ACK)


def _nak(lc):
    lc.ble_write(NAK)


def _can(lc):
    print('<- CAN')
    lc.ble_write(CAN)
    lc.ble_write(CAN)
    lc.ble_write(CAN)


def _frame_check_crc(lc):
    data = lc.dlg.x_buf[3:-2]
    rx_crc = lc.dlg.x_buf[-2:]
    calc_crc_int = crc16.crc16xmodem(data)
    calc_crc_bytes = calc_crc_int.to_bytes(2, byteorder='big')
    return calc_crc_bytes == rx_crc


class XModemException(Exception):
    pass
