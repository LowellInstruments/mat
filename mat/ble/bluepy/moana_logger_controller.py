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
        # map caller function to expected answer
        cf = str(stack()[1].function)

        # 'file_get' works differently
        assert cf != 'file_get'

        m = {
            'ping': b'ping_made_up_command',
            'auth': b'*Xa{"Authenticated":true}',
            'time_sync': a.encode(),
            'file_info': a.encode(),
            'file_clear': b'*Vc{"ArchiveBit":false}'
        }

        # long timeout
        till = time.perf_counter() + 10
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

            # re-shape timeout
            if self.per.waitForNotifications(.01):
                till = time.perf_counter() + 2

    def ping(self):
        # made-up command, needed or Moana won't answer
        self._clear_buffers()
        self._ble_tx(b'...')
        self._wait_answer()
        return self.dlg.buf

    def auth(self) -> bool:
        for i in range(3):
            self._clear_buffers()
            self._ble_tx(b'*EA123')
            self._wait_answer()
            if self.dlg.buf == b'*Xa{"Authenticated":true}':
                return True
            time.sleep(2)

    def file_info(self):
        self._clear_buffers()
        self._ble_tx(b'*BF')
        self._wait_answer('ArchiveBit')
        # a: b'*004dF\x00{"FileName":"x.csv","FileSizeEstimate":907,"ArchiveBit":"+"}'
        a = self.dlg.buf.decode()

        try:
            i_colon = a.index(':') + 2
            i_comma = a.index(',') - 1
            file_name = a[i_colon:i_comma]
            self.sn = file_name.split('_')[1]
            return file_name

        except (AttributeError, ValueError):
            # moana sometimes fails here
            return

    def file_get(self):
        # simply accumulate for a while
        self._clear_buffers()
        self._ble_tx(b'*BB')
        while self.per.waitForNotifications(3):
            pass
        return self.dlg.buf

    def file_clear(self):
        # delete senor file and stops advertising
        self._clear_buffers()
        self._ble_tx(b'*BC')
        self._wait_answer()
        return self.dlg.buf == b'*Vc{"ArchiveBit":false}'

    @staticmethod
    def file_save(data) -> str:
        if not data:
            return ''
        t = int(time.time())
        name = '/tmp/moana_{}.bin'.format(t)
        with open(name, 'wb') as f:
            f.write(data)
        return name

    def time_sync(self) -> bool:
        self._clear_buffers()
        # time() -> epoch seconds in UTC
        # src: www.tutorialspoint.com/python/time_time.htm
        epoch_s = str(int(time.time()))
        t = '*LT{}'.format(epoch_s).encode()
        self._ble_tx(t)
        self._wait_answer(epoch_s)
        return epoch_s.encode() in self.dlg.buf

    def file_cnv(self, name, dst_fol, length):
        if not os.path.isfile(name):
            print('can\'t find {} to convert'.format(name))
            return False

        # find '\x03' byte
        with open(name, 'rb') as f:
            content = f.read()
            i = content.find(b'\x03')
        if i == 0:
            return

        # get first timestamp as integer and pivot
        # saves file w/ UTC times (local when tz=None)
        i_ts = int(struct.unpack('<i', content[i+1:i+5])[0])
        first_dt = datetime.datetime.fromtimestamp(i_ts, tz=timezone.utc)
        first_dt = first_dt.strftime('%Y%m%dT%H%M%S')

        # use timestamps for file naming
        nt = '/moana_{}_{}_Temperature.csv'.format(self.sn, first_dt)
        nt = str(pathlib.Path(dst_fol)) + nt
        np = '/moana_{}_{}_Pressure.csv'.format(self.sn, first_dt)
        np = str(pathlib.Path(dst_fol)) + np
        ft = open(nt, 'w')
        fp = open(np, 'w')
        ft.write('ISO 8601 Time,Temperature (C)\n')
        fp.write('ISO 8601 Time,Pressure (dbar)\n')
        print('converting {}'.format(name))
        # print('    -> {}'.format(nt))
        # print('    -> {}'.format(np))

        # skip first timestamp
        j = i + 5

        # loop through data
        submerged = False
        while 1:
            if j + 6 > length:
                break
            line = content[j:j+6]
            i_last_ts = int(struct.unpack('<H', line[0:2])[0])
            i_ts += i_last_ts

            # saves file w/ UTC times (local when tz=None)
            # & removes the +00:00 part
            dt = datetime.datetime.fromtimestamp(i_ts, tz=timezone.utc)
            # todo > is next line needed?
            dt = dt.replace(tzinfo=None)
            press = int(struct.unpack('<H', line[2:4])[0])
            temp = int(struct.unpack('<H', line[4:6])[0])
            press = '{:4.2f}'.format((press / 10) - 10)
            temp = '{:4.2f}'.format((temp / 1000) - 10)
            j += 6
            dt = dt.isoformat('T', 'milliseconds')
            ft.write('{},{}\n'.format(dt, temp))
            fp.write('{},{}\n'.format(dt, press))
            # print('{} | {}\t{}'.format(dt, press, temp))

            # detect immersions
            p = int(float(press))
            threshold_meters = 2
            if not submerged and p > threshold_meters:
                submerged = True
                print('sub at', dt)
            elif submerged and p <= threshold_meters:
                submerged = False
                print('air at', dt)

        ft.close()
        fp.close()

        # prefix: 'moana_0113_20211206T144237'
        prefix = 'moana_{}_{}'.format(self.sn, first_dt)
        return prefix
