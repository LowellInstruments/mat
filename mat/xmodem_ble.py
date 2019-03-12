import time
import crc16


MAX_RETRANSMISSIONS = 25
SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'
NAK = b'\x15'


def xmodem_get_file(lc_ble):
    # purge: collect potential previous downloads remains
    _xmodem_purge(lc_ble, 1)

    # start: xmodem protocol
    whole_file = bytes()
    retries = 0
    sending_c = True
    while True:
        # send 'C' only if the first packet
        _xmodem_send_c_if_required(lc_ble, sending_c)

        # check: control stage, one byte required
        end_time = time.time() + 1
        _xmodem_wait_control_byte(lc_ble, end_time)

        # check: control stage received control byte in time
        if time.time() > end_time:
            return False, 1

        # good: no timeout receiving control byte
        control_byte, frame_len = _xmodem_get_control_byte(lc_ble)
        if control_byte == EOT:
            return True, whole_file
        if control_byte == CAN:
            _xmodem_can(lc_ble)
            return False, 2

        # check: receiving bytes during frame stage
        end_time = time.time() + 1
        retries = _xmodem_wait_frame(lc_ble, frame_len, retries, end_time)

        # check: frame stage received data in time
        ok, code = _xmodem_frame_timeout(lc_ble, sending_c, retries, end_time)
        if not ok:
            return ok, code
        else:
            if code == 1:
                continue

        # good: received enough during frame stage to check crc
        bunch = _xmodem_get_frame(lc_ble, sending_c, retries, whole_file)
        sending_c, retries, whole_file = bunch


def _xmodem_send_c_if_required(lc_ble, sending_c):
    lc_ble.delegate.x_buffer = bytes()
    if sending_c:
        print('c', end='')
        lc_ble.write(b'C')


def _xmodem_wait_control_byte(lc_ble, timeout):
    while True:
        if time.time() > timeout:
            break
        lc_ble.peripheral.waitForNotifications(1)
        if len(lc_ble.delegate.x_buffer) >= 1:
            break


def _xmodem_get_control_byte(lc_ble):
    # good: continue or finish
    control_byte = bytes([lc_ble.delegate.x_buffer[0]])
    if control_byte == SOH:
        return SOH, 128 + 5
    elif control_byte == STX:
        return STX, 1024 + 5
    elif control_byte == EOT:
        print('v', end='')
        _xmodem_ack(lc_ble)
        return EOT, None
    # bad: received CAN or strange control byte, should not happen
    else:
        print('w', end='')
        return CAN, None


def _xmodem_wait_frame(lc_ble, frame_len, retries, timeout):
    while True:
        if time.time() > timeout:
            retries += 1
            break
        lc_ble.peripheral.waitForNotifications(0.01)
        if len(lc_ble.delegate.x_buffer) >= frame_len:
            break
    return retries


def _xmodem_frame_timeout(lc_ble, sending_c, retries, timeout):
    if time.time() > timeout:
        # bad: timeout during frame stage, some retries left
        if retries < 3:
            print('f', end='')
            # last thing we sent was 'C' control byte
            if sending_c:
                return False, 3
            # last thing we sent was not 'C' control byte
            _xmodem_purge(lc_ble, 1)
            _xmodem_nak(lc_ble)
            return True, 1
        # bad: timeout during frame stage, no retries left
        else:
            print('timeout frame')
            _xmodem_can(lc_ble)
            return False, 4
    else:
        # good: no timeout during frame receiving
        return True, 0


def _xmodem_get_frame(lc_ble, sending_c, retries, whole_file):
    if _xmodem_check_crc(lc_ble):
        sending_c = False
        retries = 0
        whole_file += lc_ble.delegate.x_buffer[3:-2]
        print('.', end='')
        _xmodem_ack(lc_ble)
    else:
        print('x', end='')
        _xmodem_nak(lc_ble)
    return sending_c, retries, whole_file


def _xmodem_purge(lc_ble, during):
    end_time = time.time() + during
    while time.time() < end_time:
        lc_ble.peripheral.waitForNotifications(0.01)


def _xmodem_ack(lc_ble):
    lc_ble.write(ACK)


def _xmodem_nak(lc_ble):
    lc_ble.write(NAK)


def _xmodem_can(lc_ble):
    lc_ble.write(CAN)
    lc_ble.write(CAN)
    lc_ble.write(CAN)


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
