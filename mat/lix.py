import time
from collections import namedtuple
from math import ceil
from mat.ascii85 import ascii85_to_num

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
                              "battery "
                              "hdr_idx "
                              "cc_area "
                              "context"
                              )
        # dictionary measurements
        self.d_measurements = dict()
        # dictionary micro-headers
        self.d_mih = dict()

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
        start_time = _custom_time(self.mah.timestamp)
        _p("\tdatetime is   \t|  {}".format(start_time))
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
        print(f'\nconverting LIX file...')
        print(f'- file_name {self.file_path}')
        print(f'- file_size  {self.file_size}')
        print(f'- macro_header_length {CS}')
        print(f'- measurements_length {self.measurements_length}')
        print(f'- micro_headers_length {self.micro_headers_length}')
        calc_fs = CS + self.measurements_length + self.micro_headers_length
        assert self.file_size == calc_fs

    def convert_lix_file(self):
        try:
            assert self.file_path
            with open(self.file_path, 'rb') as f:
                self.bb = f.read()
            self._parse_file_info()
            self._parse_macro_header()
            self._parse_data()
        except (Exception, ) as ex:
            print(f'error: parse_lix_file ex -> {ex}')
            return 1

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
        _p(f"\n\t measurement\t|  detected")
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
        _p(f'\t      number\t|  {self.measurement_number}')
        _p(f'\tmask sm_time\t|  {s}')

        # in case of extended time
        # todo ---> test this
        if type(t) is bytes:
            t = int.from_bytes(t, "big")

        if self.mah.file_type.decode() in ("PRF", "TDO"):
            # todo -> get measurement length from sensor mask
            n = 10
            sen_t = mm[i + 2: i + 4]
            sen_p = mm[i + 4: i + 6]
            sen_ax = mm[i + 6: i + 8]
            sen_ay = mm[i + 8: i + 10]
            sen_az = mm[i + 10: i + 12]
            vt = _decode_sensor_measurement('T', sen_t)
            vp = _decode_sensor_measurement('P', sen_p)
            vax = _decode_sensor_measurement('Ax', sen_ax)
            vay = _decode_sensor_measurement('Ay', sen_ay)
            vaz = _decode_sensor_measurement('Az', sen_az)

            # build dictionary
            s = f'{vt},{vp},{vax},{vay},{vaz}'
            self.d_measurements[t] = s
            _p(f'\tdecoded data\t|  {s}')

        else:
            assert False

        # keep track of how many we decoded
        self.measurement_number += 1

        # return current index of measurements array
        return i + n

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

        # maybe fusion both dictionaries here


if __name__ == '__main__':
    p = '/home/kaz/Downloads/dl_bil/9999999_BIL_20240122_195627.lix'
    plf = ParserLixFile(p)
    plf.convert_lix_file()
