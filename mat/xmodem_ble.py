import time
import crc16


MAX_RETRANSMISSIONS = 25
SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'


def xmodem_get_file(lc_ble):
    retrans = MAX_RETRANSMISSIONS
    bufsz = 0
    whole_file = bytes()
    trychar = b'C'

    while True:
        something_to_rx = False
        for retry in range(16):
            # send C, which can fail, too
            if trychar:
                lc_ble.delegate.x_buffer = bytes()
                whole_file = bytes()
                lc_ble.write(trychar)
            # collect control bytes back
            _xmodem_collect(lc_ble, 1)
            c = _xmodem_inbyte(lc_ble, 0)
            # 128 bytes page incoming
            if c == SOH:
                bufsz = 128
                something_to_rx = True
                break
            # 1k size page incoming
            elif c == STX:
                bufsz = 1024
                something_to_rx = True
                break
            # end of transmission
            elif c == EOT:
                print('eot')
                lc_ble.delegate.x_buffer = bytes()
                lc_ble.write(ACK)
                return 0, whole_file
            # remote side cancelled transmission
            elif c == CAN:
                _xmodem_collect(lc_ble, 1)
                c = _xmodem_inbyte(lc_ble, 0)
                if c == CAN:
                    lc_ble.delegate.x_buffer = bytes()
                    lc_ble.write(ACK)
                    return -1, None
            # remote sent something unexpected or local did not clear ok
            else:
                _xmodem_nak(lc_ble)

        # finished 16 retries for control characters w/o success
        if not something_to_rx:
            lc_ble.delegate.x_buffer = bytes()
            lc_ble.write(CAN)
            lc_ble.write(CAN)
            lc_ble.write(CAN)
            lc_ble.delegate.xmodem_mode = False
            return -2, None

        # start receiving pages, or blocks
        trychar = 0
        len_page_plus_crc = bufsz + 5
        _xmodem_collect(lc_ble, len_page_plus_crc)

        # TIMEOUT, did not receive whole page in time, NAK to retry
        if len(lc_ble.delegate.x_buffer) != len_page_plus_crc:
            retrans -= 1
            _xmodem_nak(lc_ble)
            continue

        # whole page received, good CRC, ACK
        if _xmodem_check_crc(lc_ble):
            nseq = lc_ble.delegate.x_buffer[1]
            print('.'.format(nseq), end='')
            if not nseq % 25:
                print('\n')
            lc_ble.write(ACK)
            retrans = MAX_RETRANSMISSIONS
            whole_file += lc_ble.delegate.x_buffer[3:-2]
            lc_ble.delegate.x_buffer = bytes()
            continue
        # whole page received but bad CRC, NAK
        else:
            nseq = lc_ble.delegate.x_buffer[1]
            print('x{} '.format(nseq), end='')
            if not nseq % 25:
                print('\n')
            retrans -= 1
            # too many consecutive fails for this page
            if not retrans:
                print('exhausted page retries')
                lc_ble.write(CAN)
                lc_ble.write(CAN)
                lc_ble.write(CAN)
                lc_ble.delegate.xmodem_mode = False
                return -3, None
            # still some fails allowed for this page
            _xmodem_nak(lc_ble)
            continue


# get byte at indicated index
def _xmodem_inbyte(lc_ble, index):
    if len(lc_ble.delegate.x_buffer):
        return bytes([lc_ble.delegate.x_buffer[index]])
    return None


# collect bytes which form page
def _xmodem_collect(lc_ble, minimum):
    end_time = time.time() + 1
    while time.time() < end_time:
        lc_ble.peripheral.waitForNotifications(0.05)
        # minimum = 1 when receiving CTRL chars (SOH, SOT...), > 1 else
        if len(lc_ble.delegate.x_buffer) >= minimum:
            return True
    return False


def _xmodem_nak(lc_ble):
    print('x')
    _xmodem_collect_to_purge(lc_ble, 1)
    lc_ble.delegate.x_buffer = bytes()
    lc_ble.write(b'\x15')


# clean possible incoming full buffers
def _xmodem_collect_to_purge(lc_ble, during):
    end_time = time.time() + during
    while time.time() < end_time:
        lc_ble.peripheral.waitForNotifications(0.05)


# skip SOH, SOT, sequence numbers and CRC of frame and calculate CRC
def _xmodem_check_crc(lc_ble):
    data = lc_ble.delegate.x_buffer[3:-2]
    received_crc_bytes = lc_ble.delegate.x_buffer[-2:]
    calculated_crc_int = crc16.crc16xmodem(data)
    calculated_crc_bytes = calculated_crc_int.to_bytes(2, byteorder='big')
    if calculated_crc_bytes == received_crc_bytes:
        return True
    else:
        return False
