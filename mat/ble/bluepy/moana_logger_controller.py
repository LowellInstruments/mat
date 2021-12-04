import datetime
import json
import pathlib
from datetime import timezone
import os
import struct
import time
from inspect import stack
from json import JSONDecodeError
import bluepy
from bluepy import btle
from bluepy.btle import BTLEDisconnectError


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
        self.sn = ''

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
            'file_get': b'*0005D\x00',
            'file_clear': b'*Vc{"ArchiveBit":false}'
        }

        # long timeout
        till = time.perf_counter() + 5
        while 1:

            # absolute timeout
            if time.perf_counter() > till:
                break

            # exact answers -> auth, file_clear
            v = self.dlg.buf
            if v.endswith(m[cf]):
                # print('{} -> {}'.format(cf, v))
                break

            # mutable answers -> time_sync / file_info
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

    def file_info(self):
        self._clear_buffers()
        self._ble_tx(b'*BF')
        self._wait_answer('ArchiveBit')
        # a: b'*004dF\x00{"FileName":"x.csv","FileSizeEstimate":907,"ArchiveBit":"+"}'
        a = self.dlg.buf.decode()
        try:
            j = json.loads(a[a.index('{'):])
            self.sn = j['FileName'].split('_')[1]
            return j
        except (JSONDecodeError, ValueError):
            # moana sometimes fails here
            return

    def file_get(self):
        self._clear_buffers()
        t = time.perf_counter() + 3
        while 1:
            self._ble_tx(b'*BB')

            while self.per.waitForNotifications(.1):
                t = time.perf_counter() + 1

            if self.dlg.buf.endswith(b'*0005D\x00'):
                print('get end, len == ', len(self.dlg.buf))
                return self.dlg.buf

            if time.perf_counter() > t:
                break

    def file_clear(self):
        # delete all data in sensor
        # this also makes logger stop ADV
        self._clear_buffers()
        self._ble_tx(b'*BC')
        self._wait_answer()
        return self.dlg.buf == b'*Vc{"ArchiveBit":false}'

    def moana_end(self):
        # shuts off BLE ADV, obviously waits no answer
        self._clear_buffers()
        try:
            self._ble_tx(b'*B.')
        except BTLEDisconnectError:
            # this happens always :)
            pass
        time.sleep(2)

    @staticmethod
    def file_save(data) -> str:
        if not data:
            return ''
        t = int(time.time())
        name = '/tmp/moana_{}.bin'.format(t)
        with open(name, 'wb') as f:
            f.write(data)
        return name

    @staticmethod
    def file_interval(name):
        if not os.path.isfile(name):
            print('can\'t find {} to convert'.format(name))
            return False

        # find '\x03' byte
        with open(name, 'rb') as f:
            content = f.read()
            i = content.find(b'\x03')

        # skip ext and first timestamp
        if i == 0:
            return
        i += 1

        # todo > fix this
        while 1:
            line = content[i:i + 4]
            if not line:
                break
            interval = int(struct.unpack('<i', line)[0])
            print(interval)
            i += 6


    def time_sync(self) -> bool:
        self._clear_buffers()
        # time() -> seconds since epoch, in UTC
        # src: www.tutorialspoint.com/python/time_time.htm
        epoch_s = str(int(time.time()))
        t = '*LT{}'.format(epoch_s).encode()
        self._ble_tx(t)
        self._wait_answer(epoch_s)
        return epoch_s.encode() in self.dlg.buf

    def file_cnv(self, name, dst_fol):
        if not os.path.isfile(name):
            print('can\'t find {} to convert'.format(name))
            return False

        # find '\x03' byte
        with open(name, 'rb') as f:
            content = f.read()
            i = content.find(b'\x03')

        # skip ext and first timestamp
        if i == 0:
            return
        j = i + 5

        # get the first timestamp as integer and pivot
        ts = int(struct.unpack('<i', content[i+1:i+5])[0])

        # this saves the file with UTC times
        first_dt = datetime.datetime.fromtimestamp(ts, tz=timezone.utc)
        # this saves the file with local times
        # first_dt = datetime.datetime.fromtimestamp(ts)

        first_dt = first_dt.strftime('%Y%m%dT%H%M%S')
        nt = '/moana_{}_{}_Temperature.csv'.format(self.sn, first_dt)
        nt = str(pathlib.Path(dst_fol)) + nt
        np = '/moana_{}_{}_Pressure.csv'.format(self.sn, first_dt)
        np = str(pathlib.Path(dst_fol)) + np

        # print('input -> converting {}'.format(name))
        ft = open(nt, 'w')
        fp = open(np, 'w')
        ft.write('ISO 8601 Time,Temperature (C)\n')
        fp.write('ISO 8601 Time,Pressure (dbar)\n')

        while 1:
            line = content[j:j+6]
            if not line:
                break
            last_ts = int(struct.unpack('<H', line[0:2])[0])
            ts += last_ts

            # this saves the file with UTC times
            dt = datetime.datetime.fromtimestamp(ts, tz=timezone.utc)
            # this saves the file with local times
            # dt = datetime.datetime.fromtimestamp(ts)

            # remove the +00:00 part when considering utc
            dt = dt.replace(tzinfo=None)
            press = int(struct.unpack('<H', line[2:4])[0])
            temp = int(struct.unpack('<H', line[4:6])[0])
            press = '{:4.2f}'.format((press / 10) - 10)
            temp = '{:4.2f}'.format((temp / 1000) - 10)
            # print('{} | {}\t{}'.format(dt, press, temp))
            j += 6
            dt = dt.isoformat('T', 'milliseconds')
            ft.write('{},{}\n'.format(dt, temp))
            fp.write('{},{}\n'.format(dt, press))

        ft.close()
        fp.close()

        # print('output -> {}'.format(nt))
        # print('output -> {}'.format(np))

        # return the prefix
        return 'moana_{}'.format(self.sn)
