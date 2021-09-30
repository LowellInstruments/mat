import datetime
from datetime import timezone
import os
import struct
import time
from inspect import stack
import bluepy
from bluepy import btle
from os.path import expanduser


class LCBLEMoanaDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)
        self.buf = bytes()

    def handleNotification(self, c_handle, data):
        self.buf += data


class LoggerControllerMoana:

    UUID_W = btle.UUID('569a2001-b87f-490c-92cb-11ba5ea5167c')
    UUID_R = btle.UUID('569a2000-b87f-490c-92cb-11ba5ea5167c')
    UUID_S = btle.UUID('569a1101-b87f-490c-92cb-11ba5ea5167c')

    def _clear_buffers(self):
        self.dlg.buf = bytes()

    def __init__(self, mac):
        self.mac = mac
        self.per = None
        self.svc = None
        self.c_r = None
        self.c_w = None
        self.dlg = LCBLEMoanaDelegate()

    def _ble_tx(self, data):
        self.c_w.write(data, withResponse=True)

    def open(self):
        try:
            t_r = btle.ADDR_TYPE_RANDOM
            self.per = bluepy.btle.Peripheral(self.mac, t_r, timeout=10)
            self.per.setDelegate(self.dlg)
            self.svc = self.per.getServiceByUUID(self.UUID_S)
            self.c_r = self.svc.getCharacteristics(self.UUID_R)[0]
            self.c_w = self.svc.getCharacteristics(self.UUID_W)[0]
            desc = self.c_r.valHandle + 1
            self.per.writeCharacteristic(desc, b'\x01\x00')
            return True

        except (AttributeError, bluepy.btle.BTLEException) as ex:
            print('[ BLE ] can\'t connect: {}'.format(ex))

    def close(self):
        try:
            self.per.disconnect()
            self.per = None
        except AttributeError:
            pass

    def _wait_answer(self, c=''):
        # map c_f: caller function to (timeout, good answer)
        c_f = str(stack()[1].function)
        m = {
            'auth': (10, b'*Xa{"Authenticated":true}'),
            'time_sync': (10, c.encode()),
            'file_info': (10, c.encode()),
            # todo: 10 works for small file downloads
            # you must calculate the timeout for big ones
            'file_get': (10, b'*0005D\x00')
        }

        # accumulate answers
        till = time.perf_counter() + m[c_f][0]
        while 1:
            if time.perf_counter() > till:
                break

            # for 'auth' answers
            if self.dlg.buf.endswith(m[c_f][1]):
                print('    ans {} -> '.format(c_f), end='')
                break

            # for 'time_sync' / 'file_info' answers
            if c and c.encode() in self.dlg.buf:
                print('    ans {} -> '.format(c_f), end='')
                break
            self.per.waitForNotifications(.1)

        # sleep between commands
        time.sleep(.5)

    def auth(self):
        self._clear_buffers()
        self._ble_tx(b'*EA123')
        self._wait_answer()
        return self.dlg.buf

    def time_sync(self):
        self._clear_buffers()
        epoch_s = str(int(time.time()))
        t = '*LT{}'.format(epoch_s).encode()
        self._ble_tx(t)
        self._wait_answer(epoch_s)
        return self.dlg.buf

    def file_info(self):
        self._clear_buffers()
        self._ble_tx(b'*BF')
        self._wait_answer('ArchiveBit')
        return self.dlg.buf

    def file_get(self):
        print('downloading file...')
        self._clear_buffers()
        self._ble_tx(b'*BB')
        self._wait_answer()
        return self.dlg.buf

    @staticmethod
    def file_save(data) -> str:
        if not data:
            return ''
        t = int(time.time())
        home = expanduser("~")
        name = '{}/Downloads/file_{}.csv'.format(home, t)
        print('saving data to {}'.format(name))
        with open(name, 'wb') as f:
            f.write(data)
        return name

    @staticmethod
    def file_cnv(name) -> bool:
        if not os.path.isfile(name):
            print('can\'t find {} to convert'.format(name))
            return
        print('converting file {}...'.format(name))

        # find '\x03' byte
        with open(name, 'rb') as f:
            content = f.read()
            i = content.find(b'\x03')

        # skip ext and first timestamp
        if i == 0:
            return
        j = i + 5

        # get the first timestamp as integer
        ts = int(struct.unpack('<i', content[i+1:i+5])[0])

        while 1:
            line = content[j:j+6]
            if not line:
                return False
            last_ts = int(struct.unpack('<H', line[0:2])[0])
            ts += last_ts
            dt = datetime.datetime.fromtimestamp(ts, tz=timezone.utc)
            # remove the +00:00 part when considering utc
            dt = dt.replace(tzinfo=None)
            press = int(struct.unpack('<H', line[2:4])[0])
            temp = int(struct.unpack('<H', line[4:6])[0])
            press = '{:4.2f}'.format((press / 10) - 10)
            temp = '{:4.2f}'.format((temp / 1000) - 10)
            print('{} | {}\t{}'.format(dt, press, temp))
            j += 6

        return True


if __name__ == '__main__':
    lc = LoggerControllerMoana('whatever')
    lc.file_cnv('/root/Downloads/file_1632762268.csv')
