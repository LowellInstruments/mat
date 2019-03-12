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
    retransmissions = 0
    sending_c = True
    while True:
        # send 'C' only if the first packet
        lc_ble.delegate.x_buffer = bytes()
        if sending_c:
            print('c', end='')
            lc_ble.write(b'C')

        # check: receiving byte at control stage
        end_time = time.time() + 1
        while True:
            if time.time() > end_time:
                retries += 1
                break
            lc_ble.peripheral.waitForNotifications(1)
            if len(lc_ble.delegate.x_buffer) >= 1:
                break

        # check: timeouts control stage, won't enter if single byte received
        if time.time() > end_time:
            # bad: timeout during control stage, but retries left
            if retries < 3:
                print('k', end='')
                # not received any answer to our last 'C' control byte, restart
                    _xmodem_purge(lc_ble, 1)
                    _xmodem_nak(lc_ble)
                # not received any answer to our last, non-'C', control byte
                else:
                    _xmodem_nak(lc_ble)
                continue
            # bad: timeout during control stage, no retries left
            else:
                print('timeout control')
                _xmodem_can(lc_ble)
                return False, 1

        # good: no timeout receiving control byte, let's continue
        control_byte = bytes([lc_ble.delegate.x_buffer[0]])
        if control_byte == SOH:
            retries = 0
            frame_len = 128 + 5
        elif control_byte == STX:
            retries = 0
            frame_len = 1024 + 5
        elif control_byte == EOT:
            print('v', end='')
            _xmodem_ack(lc_ble)
            return True, whole_file
        # bad: received CAN or strange control byte, should not happen
        else:
            print('w', end='')
            print(control_byte)
            _xmodem_can(lc_ble)
            return False, 2

        # check: receiving bytes during frame stage
        end_time = time.time() + 1
        while True:
            if time.time() > end_time:
                retransmissions += 1
                break
            lc_ble.peripheral.waitForNotifications(0.01)
            if len(lc_ble.delegate.x_buffer) >= frame_len:
                break

        # check: timeouts during frame stage
        if time.time() > end_time:
            # bad: timeout during frame stage, some retransmissions left
            if retransmissions < 3:
                print('f', end='')
                _xmodem_purge(lc_ble, 1)
                # not received enough answer after our last 'C' control byte
                if sending_c:
                    # just purged
                    _xmodem_nak(lc_ble)
                # not received enough answer after our last non-C control byte
                else:
                    _xmodem_nak(lc_ble)
                continue
            # bad: timeout during frame stage, no retransmissions left
            else:
                print('timeout frame')
                _xmodem_nak(lc_ble)
                return False, 3

        # good: received enough during frame stage to check crc
        if _xmodem_check_crc(lc_ble):
            sending_c = False
            retransmissions = 0
            whole_file += lc_ble.delegate.x_buffer[3:-2]
            print('.', end='')
            _xmodem_ack(lc_ble)
        else:
            _xmodem_nak(lc_ble)


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
