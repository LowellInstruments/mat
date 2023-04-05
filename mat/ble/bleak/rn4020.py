import asyncio
from mat.ble.ble_mat_utils import DDH_GUI_UDP_PORT, \
    ble_mat_progress_dl
from mat.ble.bleak.rn4020_base import BleRN4020Base, UUID_T


SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
CAN = b'\x18'
NAK = b'\x15'


def _crc16(data):
    crc = 0x0000
    length = len(data)
    for i in range(0, length):
        crc ^= data[i] << 8
        for j in range(0, 8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    v = crc & 0xFFFF
    return v.to_bytes(2, 'big')


def _xmd_frame_check_crc(b):
    rx_crc = b[-2:]
    data = b[3:-2]
    calc_crc = _crc16(data)
    # print(rx_crc, calc_crc)
    return calc_crc == rx_crc


class BleRN4020(BleRN4020Base):
    """
    RN4020 implementation including Xmodem
    """

    def __init__(self, h, verbose=False):
        super().__init__(h)
        self.verbose = verbose

    def _p(self, s):
        if self.verbose:
            print(s)

    async def _ack(self):
        await self.cli.write_gatt_char(UUID_T, b'\x06')

    async def _nak(self):
        await self.cli.write_gatt_char(UUID_T, NAK)

    async def _can(self):
        await self.cli.write_gatt_char(UUID_T, CAN)
        await self.cli.write_gatt_char(UUID_T, CAN)
        await self.cli.write_gatt_char(UUID_T, CAN)

    async def cmd_xmodem(self, z, ip='127.0.0.1', port=DDH_GUI_UDP_PORT):
        self.ans = bytes()
        file_built = bytes()
        _rt = 0
        _len = 0
        _eot = 0

        ble_mat_progress_dl(0, z, ip, port)

        # send 'C' character, special case
        self._p('<- C')
        await self.cli.write_gatt_char(UUID_T, b'C')

        # -------------------------------------------------
        # curious, internal sleep 1 is enough, external 2
        # -------------------------------------------------
        await asyncio.sleep(1)

        while 1:

            # rx last frame failure
            if len(self.ans) == 0:
                self._p('len self.ans == 0')
                return 1, bytes()

            # look first byte in, the control one
            b = self.ans[0:1]
            if b == EOT:
                # good, finished
                self._p('-> eot')
                await self._ack()
                _eot = 1
                break

            elif b == SOH:
                self._p('-> soh')
                _len = 128 + 5

            elif b == STX:
                self._p('-> stx')
                _len = 1024 + 5

            elif b == CAN:
                # bad, canceled by remote
                e = '-> can ctrl {}'.format(b)
                self._p(e)
                await self._ack()
                return 2, bytes()

            else:
                # bad, weird control byte arrived
                self._p('<- nak')
                await self._nak()
                await asyncio.sleep(5)
                return 3, bytes()

            # rx frame OK -> check CRC
            if _xmd_frame_check_crc(self.ans):
                file_built += self.ans[3:_len - 2]
                _rt = 0
                self._p('<- ack')
                await self._ack()

                # notify GUI progress update
                ble_mat_progress_dl(len(file_built), z, ip, port)

            else:
                # PARSE DATA not OK, check retries left
                _rt += 1
                if _rt == 5:
                    self._p('<- crc CAN')
                    await self._can()
                    return 4, bytes()
                self._p('<- crc NAK')
                await self._nak()

            # next rx frame attempt
            self.ans = bytes()
            for i in range(10):
                await asyncio.sleep(0.1)
                if len(self.ans) >= _len:
                    break

        # truncate to size instead of n * 1024
        if _eot == 1:
            file_built = file_built[0:z]

        ble_mat_progress_dl(100, z, ip, port)
        return 0, file_built
