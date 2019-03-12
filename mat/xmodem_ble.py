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
    # collect to purge
    end_time = time.time() + 0.5
    while time.time() < end_time:
        lc_ble.peripheral.waitForNotifications(0.01)

    # start xmodem protocol
    whole_file = bytes()
    retries = 0
    retransmissions = 0
    sending_c = True
    while True:
        # check if first communication, otherwise ack / nak sent below
        lc_ble.delegate.x_buffer = bytes()
        if sending_c:
            print('c', end='')
            lc_ble.write(b'C')

        # get control byte stage
        end_time = time.time() + 1
        while True:
            if time.time() > end_time:
                retries += 1
                break
            lc_ble.peripheral.waitForNotifications(1)
            if len(lc_ble.delegate.x_buffer) >= 1:
                break

        # check if control stage timeouts or ok by now
        if time.time() > end_time:
            if retries < 3:
                print('k', end='')
                _xmodem_nak(lc_ble)
                break
            else:
                print('timeout control')
                _xmodem_can(lc_ble)
                return False, 1
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
        else:
            # received CAN or strange control byte
            print(control_byte)
            print('w', end='')
            _xmodem_can(lc_ble)
            return False, 2

        # receive whole frame stage
        end_time = time.time() + 1
        while True:
            if time.time() > end_time:
                retransmissions += 1
                break
            lc_ble.peripheral.waitForNotifications(0.01)
            if len(lc_ble.delegate.x_buffer) >= frame_len:
                break

        # check if frame stage timeouts CRC or ok by now
        if time.time() > end_time:
            if retransmissions < 3:
                print('f', end='')
                if not sending_c:
                    _xmodem_nak(lc_ble)
                # else:
                #     time.sleep(1)
                continue
            else:
                print('timeout frame')
                _xmodem_nak(lc_ble)
                return False, 3
        if _xmodem_check_crc(lc_ble):
            sending_c = False
            retransmissions = 0
            whole_file += lc_ble.delegate.x_buffer[3:-2]
            print('.', end='')
            _xmodem_ack(lc_ble)
        else:
            _xmodem_nak(lc_ble)


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
