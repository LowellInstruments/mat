import time
import crc16


SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'
NAK = b'\x15'


# download function, initial purge to start fresh, exception on error
def xmodem_get_file(lc_ble):
    _xmodem_purge(lc_ble, 1)
    whole_file = bytes()
    retries = 0
    sending_c = True

    while True:
        # control stage: send byte 'C' only on first packet
        _xmodem_send_c_if_required(lc_ble, sending_c)

        # control stage: wait 1st byte of incoming frame
        _xmodem_wait_control_byte(lc_ble)

        # data stage: frame arrived, check byte SOH, STX, CAN...
        control_byte, frame_len = _xmodem_get_control_byte(lc_ble)
        if control_byte == EOT:
            return True, whole_file

        # data stage: receive rest of frame, note 'end_time' is shared
        end_time = time.time() + 1
        retries = _xmodem_wait_frame(lc_ble, frame_len, retries, end_time)
        if not _xmodem_frame_timeout(lc_ble, sending_c, retries, end_time):
            bunch = _xmodem_get_frame(lc_ble, sending_c, retries, whole_file)
            sending_c, retries, whole_file = bunch


def _xmodem_send_c_if_required(lc_ble, sending_c):
    lc_ble.delegate.x_buffer = bytes()
    if sending_c:
        # print('c')
        lc_ble.ble_write(b'C')


def _xmodem_wait_control_byte(lc_ble):
    timeout = time.time() + 1
    while True:
        if time.time() > timeout:
            # happens very rarely but it does
            # print('K')
            raise XModemException('xmodem exception: waiting control byte.')
        lc_ble.peripheral.waitForNotifications(1)
        if len(lc_ble.delegate.x_buffer) >= 1:
            break


def _xmodem_get_control_byte(lc_ble):
    control_byte = bytes([lc_ble.delegate.x_buffer[0]])
    if control_byte == SOH:
        return SOH, 128 + 5
    elif control_byte == STX:
        return STX, 1024 + 5
    elif control_byte == EOT:
        # print('v')
        _xmodem_ack(lc_ble)
        return EOT, None
    # bad: received CAN or strange control byte
    else:
        # print('W' + control_byte)
        _xmodem_can(lc_ble)
        raise XModemException('xmodem exception: getting control byte.')


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
    # easier to restart than recover a lost 'C'
    if time.time() > timeout and sending_c:
        # print('I')
        raise XModemException('xmodem exception: timeout waiting frame post-C')
    # timeout, check retries left
    if time.time() > timeout and retries >= 3:
        # print('F')
        _xmodem_can(lc_ble)
        raise XModemException('xmodem exception: timeout data, 0 retries left')
    elif time.time() > timeout and retries < 3:
        # print('f', end='')
        _xmodem_purge(lc_ble, 1)
        _xmodem_nak(lc_ble)
        # bad: timeout
        return True
    # nice: no timeout during frame receiving
    return False


def _xmodem_get_frame(lc_ble, sending_c, retries, whole_file):
    # print(lc_ble.delegate.x_buffer)
    if _xmodem_check_crc(lc_ble):
        sending_c = False
        retries = 0
        whole_file += lc_ble.delegate.x_buffer[3:-2]
        # print('.', end='')
        _xmodem_ack(lc_ble)
    else:
        # print('x', end='')
        _xmodem_nak(lc_ble)
    return sending_c, retries, whole_file


def _xmodem_purge(lc_ble, during):
    end_time = time.time() + during
    while time.time() < end_time:
        lc_ble.peripheral.waitForNotifications(0.01)


def _xmodem_ack(lc_ble):
    lc_ble.ble_write(ACK)


def _xmodem_nak(lc_ble):
    lc_ble.ble_write(NAK)


def _xmodem_can(lc_ble):
    lc_ble.ble_write(CAN)
    lc_ble.ble_write(CAN)
    lc_ble.ble_write(CAN)


# calculate CRC omitting proper fields
def _xmodem_check_crc(lc_ble):
    data = lc_ble.delegate.x_buffer[3:-2]
    received_crc_bytes = lc_ble.delegate.x_buffer[-2:]
    calculated_crc_int = crc16.crc16xmodem(data)
    calculated_crc_bytes = calculated_crc_int.to_bytes(2, byteorder='big')
    # print(len(lc_ble.delegate.x_buffer))
    if calculated_crc_bytes == received_crc_bytes:
        return True
    else:
        return False


# xmodem fatal exceptions controlled on app, this file controls non fatal ones
class XModemException(Exception):
    pass
