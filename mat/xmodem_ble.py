import time
import crc16


MAX_RETRANSMISSIONS = 25
SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'
NAK = b'\x15'


# main receive file, first purge cleans previous download buffers
def xmodem_get_file(lc_ble):
    _xmodem_purge(lc_ble, 1)

    # xmodem: start protocol
    whole_file = bytes()
    retries = 0
    sending_c = True
    while True:
        # send control byte 'C' only on first packet
        _xmodem_send_c_if_required(lc_ble, sending_c)

        # control stage: one byte required to be received
        _xmodem_wait_control_byte(lc_ble)

        # good: no timeout during control byte
        control_byte, frame_len = _xmodem_get_control_byte(lc_ble)
        if control_byte == EOT:
            return True, whole_file

        # check: receive data during frame stage
        end_time = time.time() + 1
        retries = _xmodem_wait_frame(lc_ble, frame_len, retries, end_time)

        # check: received data in time during frame stage
        if not _xmodem_frame_timeout(lc_ble, sending_c, retries, end_time):
            # good: received enough during frame stage to check crc
            bunch = _xmodem_get_frame(lc_ble, sending_c, retries, whole_file)
            sending_c, retries, whole_file = bunch


# protocol triggering if we are starting
def _xmodem_send_c_if_required(lc_ble, sending_c):
    lc_ble.delegate.x_buffer = bytes()
    if sending_c:
        # print('c', end='')
        lc_ble.write(b'C')


# wait for the first byte in incoming frame, if any
def _xmodem_wait_control_byte(lc_ble):
    timeout = time.time() + 1
    while True:
        # timeout: we did not even receive a single byte back
        if time.time() > timeout:
            # this happens very rarely but it does
            # print('K')
            raise XModemException('xmodem: timeout waiting control byte')
        lc_ble.peripheral.waitForNotifications(1)
        if len(lc_ble.delegate.x_buffer) >= 1:
            return


# control decision, may be cancelling, ending ok or just receiving data frame
def _xmodem_get_control_byte(lc_ble):
    # good: continue or finish
    control_byte = bytes([lc_ble.delegate.x_buffer[0]])
    if control_byte == SOH:
        return SOH, 128 + 5
    elif control_byte == STX:
        return STX, 1024 + 5
    elif control_byte == EOT:
        # print('v', end='')
        _xmodem_ack(lc_ble)
        return EOT, None
    # bad: received CAN or strange control byte, should not happen
    else:
        # print('W')
        raise XModemException('what is this?')


# wait for the rest of the data in the frame besides the control byte
def _xmodem_wait_frame(lc_ble, frame_len, retries, timeout):
    while True:
        if time.time() > timeout:
            retries += 1
            break
        lc_ble.peripheral.waitForNotifications(0.01)
        if len(lc_ble.delegate.x_buffer) >= frame_len:
            break
    return retries


# continue if we have enough data
def _xmodem_frame_timeout(lc_ble, sending_c, retries, timeout):
    # easier to restart than recover a 'C'
    if time.time() > timeout and sending_c:
        # print('I')
        raise XModemException('xmodem: timeout waiting initial frame after C')
    # timeout, check if we have retries left
    if time.time() > timeout and retries >= 3:
        # print('F')
        _xmodem_can(lc_ble)
        raise XModemException('xmodem: timeout waiting frame, no retries left')
    elif time.time() > timeout and retries < 3:
        # print('f', end='')
        _xmodem_purge(lc_ble, 1)
        _xmodem_nak(lc_ble)
        return True
    # good: no timeout during frame receiving
    return False


# collect the frame with enough data if its CRC is ok
def _xmodem_get_frame(lc_ble, sending_c, retries, whole_file):
    if _xmodem_check_crc(lc_ble):
        sending_c = False
        retries = 0
        whole_file += lc_ble.delegate.x_buffer[3:-2]
        #print('.', end='')
        _xmodem_ack(lc_ble)
    else:
        #print('x', end='')
        _xmodem_nak(lc_ble)
    return sending_c, retries, whole_file


# clean xmodem buffers
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


# calculate CRC omitting proper fields
def _xmodem_check_crc(lc_ble):
    data = lc_ble.delegate.x_buffer[3:-2]
    received_crc_bytes = lc_ble.delegate.x_buffer[-2:]
    calculated_crc_int = crc16.crc16xmodem(data)
    calculated_crc_bytes = calculated_crc_int.to_bytes(2, byteorder='big')
    if calculated_crc_bytes == received_crc_bytes:
        return True
    else:
        return False


# xmodem fatal exceptions controlled on app, this file controls non fatal ones
class XModemException(Exception):
    pass
