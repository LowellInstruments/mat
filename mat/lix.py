import os
import traceback
from collections import namedtuple
from math import ceil
from mat.ascii85 import ascii85_to_num
from mat.pressure import Pressure
from mat.temperature import Temperature
from functools import lru_cache
from dateutil.tz import tzlocal, tzutc
import datetime


# debug
g_verbose = True

# chunk size
CS = 256
# micro-header size
UHS = 8
# flag debug
debug = 0
# lengths
LEN_CC_AREA = 29 * 5
LEN_CF_AREA = 13 * 5
LEN_CONTEXT = 64


def _p(s, **kwargs):
    if g_verbose:
        print(s, **kwargs)


def _show_bytes(bb: bytes, length: int):
    for i, b in enumerate(bb):
        if i % length == 0:
            _p('')
        _p('{:02x} '.format(b), end='')
    _p('')


def _custom_time(b: bytes) -> str:
    s = ''
    for v in b:
        high = (v & 0xf0) >> 4
        low = (v & 0x0f) >> 0
        s += f'{high}{low}'
    return s


def _decode_sensor_measurement(s, x):
    # x: b'\xff\xeb'
    # s: 'T', 'P', 'Ax'...
    def _c2_to_decimal(n):
        if not (n & 0x8000):
            # detect positive numbers
            return n
        c2 = (-1) * (65535 + 1 - n)
        return c2

    # big endian to int
    v = int.from_bytes(x, "big")
    if 'A' in s:
        # v: 65515
        v = _c2_to_decimal(v)
    return v


def _parse_macro_header_start_time_to_seconds(s: str) -> int:
    # s: '231103190012' embedded in macro_header
    dt = datetime.datetime.strptime(s, "%y%m%d%H%M%S")
    # set dt as UTC since objects are 'naive' by default
    dt_utc = dt.replace(tzinfo=tzutc())
    dt_utc.astimezone(tzlocal())
    rv = dt_utc.timestamp()
    # rv: 1699038012
    return int(rv)


def _seconds_between_two_time_str(a, b, fmt='%Y-%m-%dT%H:%M:%S.000'):
    dt_a = datetime.datetime.strptime(a, fmt)
    dt_b = datetime.datetime.strptime(b, fmt)
    return (dt_b - dt_a).total_seconds()


class LixFileConverterT:
    def __init__(self, a, b, c, d, r):
        self.coefficients = dict()
        self.coefficients['TMA'] = a
        self.coefficients['TMB'] = b
        self.coefficients['TMC'] = c
        self.coefficients['TMD'] = d
        self.coefficients['TMR'] = r
        self.cnv = Temperature(self)

    @lru_cache
    def convert(self, raw_temperature):
        return self.cnv.convert(raw_temperature)


class LixFileConverterP:
    def __init__(self, a, b):
        # the converter outputs decibars
        # 1 dbar = 1.45 psi
        self.coefficients = dict()
        self.coefficients['PRA'] = a
        self.coefficients['PRB'] = b
        self.cnv = Pressure(self)

    @lru_cache
    def convert(self, raw_pressure):
        return self.cnv.convert(raw_pressure)


# ---------------------------------------------------------------
# the LIX file format, chunks are 256 bytes long
# chunk #0 is just a macro-header
#     [    0 .. 2] = file descriptor = "TDO"
#     [         3] = file version = 1
#     [    4 .. 9] = epoch = '2023/11/03 18:42:00' = 231103184200
#     [  10 .. 11] = battery measurement
#     [        12] = header index = 0 on macro-header
#                x = CC_AREA_LEN
#     [13 .. 13+x] = host storage area, length = x, calibration P, T...
#               y = CONTEXT_LEN
#     [256-y..223] = fw version "a.b.cd", save as "abcd"
#     [       224] = rvn
#     [       225] = pfm
#     [       226] = spn
#     [       227] = pma
#     [228 .. 231] = SPT_us
#     [232 .. 235] = DRO_us
#     [236 .. 238] = DRU_us
#     [239 .. 240] = DRF_us
#     [241 .. 244] = DCO
#     [245 .. 247] = DHU
# other chunks are a micro-header + data
#         [0 .. 1] = battery measurement
#         [     2] = header index
#         [     3] = effective chunk length
#         [4 .. 7] = seconds since we started
# ---------------------------------------------------------------


class ParserLixFile:
    def __init__(self, file_path):
        self.debug = debug
        self.file_path = file_path
        # all file bytes
        self.bb = bytes()
        # meta-data calculated at beginning
        self.file_size = 0
        self.measurements_length = 0
        self.micro_headers_length = 0
        self.measurement_number = 0
        # sm: sensor mask
        self.sm = None
        # named tuple macro-header
        self.mah = namedtuple("MacroHeader",
                              "bytes "
                              "file_type "
                              "file_version "
                              "timestamp "
                              "timestamp_str "
                              "battery "
                              "hdr_idx "
                              "cc_area "
                              "context"
                              )
        # dictionary measurements
        self.d_measurements = dict()
        # dictionary micro-headers
        self.d_mih = dict()

    def _parse_file_info(self):
        # calculate number of file chunks
        n = ceil(len(self.bb) / CS)

        # file_size: remove last chunk contribution
        file_size = (n - 1) * CS
        # file_size: calculate last chunk contribution
        last_ecl = CS - self.bb[-CS:][3]
        self.file_size = file_size + last_ecl

        # measurements length: remove first and last chunk contribution
        self.measurements_length = (n - 2) * (CS - UHS)
        self.measurements_length += (last_ecl - UHS)

        # micro_headers length calculation
        self.micro_headers_length = (n - 1) * UHS

        # display file info
        pad = '\t'
        _p('\n')
        _p("-----------------------------------------------------------------")
        _p(f'converting LIX file...')
        _p(f'{pad}file_name:            {os.path.basename(self.file_path)}')
        _p(f'{pad}file_size:            {self.file_size}')
        _p(f'{pad}macro_header_length:  {CS}')
        _p(f'{pad}measurements_length:  {self.measurements_length}')
        _p(f'{pad}micro_headers_length: {self.micro_headers_length}')
        _p("-----------------------------------------------------------------")
        calc_fs = CS + self.measurements_length + self.micro_headers_length
        assert self.file_size == calc_fs

    def _parse_macro_header(self):
        self.mah.bytes = self.bb[:CS]
        bb = self.mah.bytes
        # todo ---> unhardcode this
        self.mah.file_type = bb[:3]
        self.mah.file_version = bb[3]
        self.mah.timestamp = bb[4:10]
        self.mah.battery = bb[10:12]
        self.mah.hdr_idx = bb[12]
        # HSA macro-header must match firmware hsa.h
        i_mah = 13
        self.mah.cc_area = bb[i_mah: i_mah + LEN_CC_AREA]
        # context
        i = CS - LEN_CONTEXT
        self.mah.context = bb[i:]
        gfv = bb[i:i+4]
        i += 4
        rvn = bb[i]
        i += 1
        pfm = bb[i]
        i += 1
        spn = bb[i]
        i += 1
        pma = bb[i]
        i += 1
        spt = bb[i:i + 5].decode()
        i += 5
        dro = bb[i:i + 5].decode()
        i += 5
        dru = bb[i:i + 5].decode()
        i += 5
        drf = bb[i:i + 2].decode()
        i += 2
        dco = bb[i:i + 5].decode()
        i += 5
        dhu = bb[i:i + 3].decode()
        i += 3
        psm = bb[i:i + 5].decode()

        # display all this info
        _p(f"\n\tMACRO header \t|  logger type {self.mah.file_type.decode()}")
        _p(f"\tfile version \t|  {self.mah.file_version}")
        self.mah.timestamp_str = _custom_time(self.mah.timestamp)
        _p("\tdatetime is   \t|  {}".format(self.mah.timestamp_str))
        bat = int.from_bytes(self.mah.battery, "big")
        _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        _p(f"\theader index \t|  {self.mah.hdr_idx}")
        n = LEN_CC_AREA
        if b"00003" != self.mah.cc_area[:5]:
            return {}
        _p("\tcc_area \t\t|  detected")
        pad = '\t\t\t\t\t   '
        _p(f'{pad}tmr = {ascii85_to_num(self.mah.cc_area[10:15].decode())}')
        _p(f'{pad}tma = {ascii85_to_num(self.mah.cc_area[15:20].decode())}')
        _p(f'{pad}tmb = {ascii85_to_num(self.mah.cc_area[20:25].decode())}')
        _p(f'{pad}tmc = {ascii85_to_num(self.mah.cc_area[25:30].decode())}')
        _p(f'{pad}tmd = {ascii85_to_num(self.mah.cc_area[30:35].decode())}')
        _p(f'{pad}pra = {ascii85_to_num(self.mah.cc_area[n-20:n-15].decode())}')
        _p(f'{pad}prb = {ascii85_to_num(self.mah.cc_area[n-15:n-10].decode())}')
        _p(f'{pad}prc = {ascii85_to_num(self.mah.cc_area[n-10:n-5].decode())}')
        _p(f'{pad}prd = {ascii85_to_num(self.mah.cc_area[n-5:].decode())}')
        _p("\tcontext \t\t|  detected")
        _p(f'{pad}gfv = {gfv}')
        _p(f'{pad}rvn = {rvn}')
        _p(f'{pad}pfm = {pfm}')
        _p(f'{pad}spn = {spn}')
        _p(f'{pad}pma = {pma}')
        _p(f'{pad}spt = {spt}')
        _p(f'{pad}dro = {dro}')
        _p(f'{pad}dru = {dru}')
        _p(f'{pad}drf = {drf}')
        _p(f'{pad}dco = {dco}')
        _p(f'{pad}dhu = {dhu}')
        _p(f'{pad}psm = {psm}')

    def _parse_data(self):
        if self.debug:
            db = b'0' * CS
            db += b'1' * UHS
            db += b'2' * (CS - UHS)
            db += b'3' * UHS
            db += b'4' * (CS - UHS)
            self.bb = db

        # skip macro-header
        data = self.bb[CS:]
        measurements = bytes()
        micro_headers = bytes()

        # n: number of chunks, iterate them to build byte arrays
        n = ceil(len(data) / CS)
        for i in range(0, CS * n, CS):
            measurements += data[i+UHS:i+CS]
            micro_headers += data[i:i+UHS]

        # build dictionary micro_headers
        for i in range(0, UHS, len(micro_headers)):
            self._parse_data_mih(micro_headers, i)

        # build dictionary of variable-length measurements
        i = 0
        while i < self.measurements_length:
            i = self._parse_data_measurement(measurements, i)

        # debug
        # print(self.d_measurements)

    def _parse_data_mih(self, mi, i):
        # 2B battery, 1B header index % 255,
        # 1B ECL, 4B epoch
        bat = int.from_bytes(mi[:i+2], "big")
        idx = mi[i+2]
        ecl = mi[i+3]
        rt = int.from_bytes(mi[i+4:i+8], "big")
        _p(f"\n\tMICRO header \t|  detected")
        _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        _p("\theader index  \t|  0x{:02x} = {}".format(idx, idx))
        _p("\tpadding count \t|  0x{:02x} = {}".format(ecl, ecl))
        _p("\trelative time \t|  0x{:08x} = {}".format(rt, rt))
        self.d_mih[rt] = {"bat": bat, "idx": idx, "ecl": ecl}

    def _parse_data_measurement(self, mm, i):
        _p(f"\n\tmeasurement #   |  {self.measurement_number}")
        mk = (mm[i] & 0xc0) >> 6
        self.sm = None
        if mk == 0:
            # no sensor mask, time simple
            t = mm[i] & 0x3F
            i += 1
            s = 'ts 0x{:02x}'.format(t)
        elif mk == 1:
            # no sensor mask, time extended
            t = (mm[i] & 0x3F) << 8
            t += mm[i+1]
            i += 2
            s = 'te 0x{:04x}'.format(t)
        elif mk == 2:
            # yes sensor mask, time simple
            self.sm = mm[i] & 0x3F
            t = mm[i+1]
            i += 2
            s = 'sm 0x{:02x} ts 0x{:02x}'.format(self.sm, t)
        else:
            # yes sensor mask, time extended
            self.sm = mm[i] & 0x3F
            t = (mm[i] & 0x3F) << 8
            t += mm[i+1]
            i += 3
            s = 'sm 0x{:02x} te 0x{:04x}'.format(self.sm, t)

        # display mask
        _p(f'\tmask sm_time\t|  {s}')

        # in case of extended time
        # todo ---> test this extended time
        if type(t) is bytes:
            t = int.from_bytes(t, "big")

        if self.mah.file_type.decode() in ("PRF", "TDO"):
            # todo -> get measurement length from sensor mask
            n = 10
            # build dictionary
            self.d_measurements[t] = mm[i:i+n]
        else:
            assert False

        # keep track of how many we decoded
        self.measurement_number += 1

        # return current index of measurements' array
        return i + n

    def _create_csv_file(self):
        # use the calibration coefficients to create objects
        n = LEN_CC_AREA
        tmr = ascii85_to_num(self.mah.cc_area[10:15].decode())
        tma = ascii85_to_num(self.mah.cc_area[15:20].decode())
        tmb = ascii85_to_num(self.mah.cc_area[20:25].decode())
        tmc = ascii85_to_num(self.mah.cc_area[25:30].decode())
        tmd = ascii85_to_num(self.mah.cc_area[30:35].decode())
        pra = ascii85_to_num(self.mah.cc_area[n-20:n-15].decode())
        prb = ascii85_to_num(self.mah.cc_area[n-15:n-10].decode())
        lct = LixFileConverterT(tma, tmb, tmc, tmd, tmr)
        lcp = LixFileConverterP(pra, prb)

        # ---------------
        # csv file header
        # ---------------
        csv_path = (self.file_path[:-4] +
                    '_' + self.mah.file_type.decode() + '.csv')
        f_csv = open(csv_path, 'w')
        cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),' \
               'Temperature (C),Pressure (dbar),Ax,Ay,Az\n'
        f_csv.write(cols)

        # get first time
        epoch = _parse_macro_header_start_time_to_seconds(self.mah.timestamp_str)
        calc_epoch = epoch
        ct = 0
        for k, v in self.d_measurements.items():
            # {t}: {sensor_data}
            vt = _decode_sensor_measurement('T', v[0:2])
            vp = _decode_sensor_measurement('P', v[2:4])
            vax = _decode_sensor_measurement('Ax', v[4:6])
            vay = _decode_sensor_measurement('Ay', v[6:8])
            vaz = _decode_sensor_measurement('Az', v[8:10])
            vt = '{:.02f}'.format(lct.convert(vt))
            vp = '{:.02f}'.format(lcp.convert(vp)[0])

            # CSV file and DESC file with LOCAL time...
            calc_epoch += k
            # UTC time, o/wise use fromtimestamp()
            t = datetime.datetime.utcfromtimestamp(calc_epoch).isoformat() + ".000"

            # elapsed and cumulative time
            # todo ---> check this works with more than 3 samples
            et = calc_epoch - epoch
            ct += et

            # log to file
            s = f'{t},{et},{ct},{vt},{vp},{vax},{vay},{vaz}\n'
            f_csv.write(s)
            print(s)

        # close the file
        f_csv.close()

    def convert_lix_file(self):
        try:
            assert self.file_path
            with open(self.file_path, 'rb') as f:
                self.bb = f.read()
            self._parse_file_info()
            self._parse_macro_header()
            self._parse_data()
            self._create_csv_file()
        except (Exception, ) as ex:
            traceback.print_exc()
            print(f'error: parse_lix_file ex -> {ex}')
            return 1


if __name__ == '__main__':
    p = '/home/kaz/Downloads/dl_bil/9999999_BIL_20240122_195627.lix'
    plf = ParserLixFile(p)
    plf.convert_lix_file()
