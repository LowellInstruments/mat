import datetime
import json
from datetime import timezone
import os
import struct
import time
from inspect import stack
import bluepy
from bluepy import btle
from os.path import expanduser


def utils_logger_is_moana(mac, info):
    return 'MOANA' in info


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

    def __init__(self, mac, h=0):
        self.mac = mac
        self.h = h
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
            self.per = bluepy.btle.Peripheral(self.mac, iface=self.h,
                                              addrType=t_r, timeout=10)
            time.sleep(1.1)
            self.per.setDelegate(self.dlg)
            self.svc = self.per.getServiceByUUID(self.UUID_S)
            self.c_r = self.svc.getCharacteristics(self.UUID_R)[0]
            self.c_w = self.svc.getCharacteristics(self.UUID_W)[0]
            desc = self.c_r.valHandle + 1
            self.per.writeCharacteristic(desc, b'\x01\x00')
            self.per.setMTU(27)
            return True

        except (AttributeError, bluepy.btle.BTLEException) as ex:
            print('[ BLE ] can\'t connect: {}'.format(ex))

    def close(self):
        try:
            self.per.disconnect()
            self.per = None
        except AttributeError:
            pass

    def _wait_answer(self, a=''):
        # map c_f: caller function to (timeout, good answer)
        cf = str(stack()[1].function)

        m = {
            'ping': b'ping_made_up_command',
            'auth': b'*Xa{"Authenticated":true}',
            'time_sync': a.encode(),
            'file_info': a.encode(),
            'file_get': b'*0005D\x00'
        }

        # long timeout
        till = time.perf_counter() + 2
        while 1:

            # absolute timeout
            if time.perf_counter() > till:
                break

            # for 'auth' answers
            v = self.dlg.buf
            if v.endswith(m[cf]):
                # print('{} -> {}'.format(cf, v))
                break

            # for 'time_sync' / 'file_info' answers
            if a and a.encode() in v:
                # print('{} -> {}'.format(cf, v))
                break

            if self.per.waitForNotifications(.01):
                till = time.perf_counter() + 1

    def ping(self):
        # needed or Moana won't answer
        self._clear_buffers()
        self._ble_tx(b'...')
        self._wait_answer()
        return self.dlg.buf

    def auth(self) -> bool:
        self._clear_buffers()
        self._ble_tx(b'*EA123')
        self._wait_answer()
        return self.dlg.buf == b'*Xa{"Authenticated":true}'

    def time_sync(self) -> bool:
        self._clear_buffers()
        epoch_s = str(int(time.time()))
        t = '*LT{}'.format(epoch_s).encode()
        self._ble_tx(t)
        self._wait_answer(epoch_s)
        return epoch_s.encode() in self.dlg.buf

    def file_info(self):
        self._clear_buffers()
        self._ble_tx(b'*BF')
        self._wait_answer('ArchiveBit')
        # a: b'*004dF\x00{"FileName":"x.csv","FileSizeEstimate":907,"ArchiveBit":"+"}'
        a = self.dlg.buf.decode()
        j = json.loads(a[a.index('{'):])
        return j

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
            return False
        print('converting file {}...'.format(name))

        # find '\x03' byte
        with open(name, 'rb') as f:
            content = f.read()
            i = content.find(b'\x03')

        # skip ext and first timestamp
        if i == 0:
            return False
        j = i + 5

        # get the first timestamp as integer
        ts = int(struct.unpack('<i', content[i+1:i+5])[0])

        while 1:
            line = content[j:j+6]
            if not line:
                break
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
