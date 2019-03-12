import time
import crc16
import sys

MAX_RETRANSMISSIONS = 25
SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'
NAK = b'\x15'


def xmodem_get_file(lc_ble):
    retrans = MAX_RETRANSMISSIONS
    whole_file = bytes()
    trychar = b'C'

    while True:
        # start or continue xmodem protocol analyzing control bytes
        something_to_rx, bufsz = _xmodem_control(lc_ble, trychar)

        # bad: CAN because 0 retries left for control characters
        if bufsz < 0:
            _xmodem_can(lc_ble)
            return bufsz, None
        # good: potentially received whole file, check outside
        elif bufsz == 0:
            _xmodem_ack(lc_ble)
            return bufsz, whole_file
        # good: started receiving a page
        elif bufsz > 0 and something_to_rx:
            trychar = 0
        # bad: this should never happen
        else:
            return -4, None

        # start receiving pages, or blocks
        len_page_plus_crc = bufsz + 5
        _xmodem_collect(lc_ble, len_page_plus_crc)

        # bad: timeout receiving page
        if len(lc_ble.delegate.x_buffer) < len_page_plus_crc:
            retrans -= 1
            _xmodem_nak(lc_ble, 0)
            # print('fucking TIMEOUT')
            # sys.exit(-1)
            # todo: this happened... II
            continue

        # good: whole page received w/ correct CRC
        if _xmodem_check_crc(lc_ble):
            retrans = MAX_RETRANSMISSIONS
            whole_file += lc_ble.delegate.x_buffer[3:-2]
            _xmodem_ack(lc_ble)
        # bad: whole page received w/o correct CRC
        else:
            if not retrans:
                _xmodem_can(lc_ble)
                return -3, None
            retrans -= 1
            # todo: this happened... II
            # print('fucking CRC')
            # sys.exit(-1)
            _xmodem_nak(lc_ble, 0)


# xmodem control stage
def _xmodem_control(lc_ble, trychar):
    for retry in range(16):
        # send C (which can fail, too)
        if trychar:
            lc_ble.delegate.x_buffer = bytes()
            lc_ble.write(trychar)
        # receive 1 control byte back
        _xmodem_collect(lc_ble, 1)
        c = _xmodem_inbyte(lc_ble, 0)
        # ok, 128 bytes page incoming
        if c == SOH:
            return True, 128
        # ok, 1k size page incoming
        elif c == STX:
            return True, 1024
        # end of transmission
        elif c == EOT:
            return False, 0
        # remote side cancelled transmission
        elif c == CAN:
            return False, -1
        # remote sent control unexpected
        else:
            # todo: this happened... I
            # print('fucking CONTROL')
            # sys.exit(-1)
            _xmodem_nak(lc_ble, 1)
    return False, -2


# get byte at indicated index
def _xmodem_inbyte(lc_ble, index):
    if len(lc_ble.delegate.x_buffer):
        return bytes([lc_ble.delegate.x_buffer[index]])
    return None


# collect bytes which form page, minimum = 1 for ctrl bytes, >1 otherwise
def _xmodem_collect(lc_ble, minimum):
    end_time = time.time() + 1
    while time.time() < end_time:
        if lc_ble.peripheral.waitForNotifications(0.01):
            end_time = end_time + 0.01
        if len(lc_ble.delegate.x_buffer) >= minimum:
            return True
    return False


def _xmodem_nak(lc_ble, during):
    _xmodem_collect_to_purge(lc_ble, during)
    lc_ble.delegate.x_buffer = bytes()
    lc_ble.write(NAK)


def _xmodem_ack(lc_ble):
    lc_ble.delegate.x_buffer = bytes()
    lc_ble.write(ACK)


def _xmodem_can(lc_ble):
    lc_ble.write(CAN)
    lc_ble.write(CAN)
    lc_ble.write(CAN)
    #todo: remove this


# clean possible incoming full buffers
def _xmodem_collect_to_purge(lc_ble, during):
    end_time = time.time() + during
    while time.time() < end_time:
        lc_ble.peripheral.waitForNotifications(0.01)


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
