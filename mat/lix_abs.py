import os
from abc import abstractmethod, ABC
from collections import namedtuple
from math import ceil
from dateutil.tz import tzlocal, tzutc
import datetime
from datetime import timezone


# size of a LIX file chunk and alternative shorter name
LEN_LIX_FILE_CHUNK = 256
CS = LEN_LIX_FILE_CHUNK

# size of a LIX file micro-header inside a chunk and alternative shorter name
LEN_LIX_FILE_MICRO_HEADER = 8
UHS = LEN_LIX_FILE_MICRO_HEADER


# memory area in firmware storing calibration constants
LEN_LIX_FILE_CC_AREA = 5 * 29

# memory area in firmware storing profiling constants
LEN_LIX_FILE_CF_AREA = 5 * 13

# length in lix file that we reserve to store compressed CF_AREA
# instead of 5 * 13 = 65, we store around 40 bytes
LEN_LIX_FILE_CONTEXT = 64


# debug
g_verbose = True
debug = 0


def _p(s, **kwargs):
    if g_verbose:
        print(s, **kwargs)


def _show_bytes(bb: bytes, length: int):
    for i, b in enumerate(bb):
        if i % length == 0:
            _p('')
        _p('{:02x} '.format(b), end='')
    _p('')


def _mah_time_to_str(b: bytes) -> str:
    # b: b'\x24\x01\x31\x12\x34\x56'
    s = ''
    for v in b:
        high = (v & 0xf0) >> 4
        low = (v & 0x0f) >> 0
        s += f'{high}{low}'
    # s: '240131123456'
    return s


def _mah_time_utc_epoch(b: bytes) -> int:
    # b: b'\x24\x01\x31\x12\x34\x56'
    # s: '240131123456'
    s = _mah_time_to_str(b)
    fmt = '%y%m%d%H%M%S'
    t = datetime.datetime.strptime(s, fmt)
    u = t.replace(tzinfo=timezone.utc).timestamp()
    return int(u)


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


def _raw_sensor_measurement(x):
    # x: b'\xff\xeb'
    # s: 'T', 'P', 'Ax'...
    # big endian to int
    return int.from_bytes(x, "big")


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


class ParserLixFile(ABC):
    def __init__(self, file_path):
        self.debug = debug
        self.file_path = file_path
        # all file bytes
        self.bb = bytes()
        # meta-data calculated at beginning
        self.len_file = 0
        self.len_mm = 0
        self.len_uh = 0
        # measurement number
        self.mm_i = 0
        # sm: sensor mask
        self.sm = None
        # named tuple macro-header
        self.mah = namedtuple(
            "MacroHeader",
            "bytes "
            "file_type "
            "file_version "
            "timestamp "
            "timestamp_str "
            "timestamp_epoch "
            "battery "
            "hdr_idx "
            "cc_area "
        )
        self.mah_context = namedtuple(
            "MacroHeader_Context",
            "bytes "
            "spt "
            "spn "
            "psm "
        )
        # dictionary measurements
        self.d_mm = dict()
        # dictionary micro-headers
        self.d_uh = dict()

    def _load_file_bytes(self):
        with open(self.file_path, 'rb') as f:
            self.bb = f.read()

    def _get_file_length(self):
        # n: number of file chunks
        n = ceil(len(self.bb) / CS)

        # file_size: calculate last chunk contribution
        file_size = (n - 1) * CS
        last_ecl = CS - self.bb[-CS:][3]
        self.len_file = file_size + last_ecl

        # measurements length: remove first and last chunk contribution
        self.len_mm = (n - 2) * (CS - UHS)
        self.len_mm += (last_ecl - UHS)

        # micro_headers length calculation
        self.len_uh = (n - 1) * UHS

        # display file info
        pad = '\t'
        bn = os.path.basename(self.file_path)
        _p('\n')
        _p("----------------------------------------------------")
        _p(f'converting LIX file:')
        _p(f'{pad}name           {bn}')
        _p(f'{pad}size           {self.len_file}')
        _p(f'{pad}len_macro_h    {CS}')
        _p(f'{pad}len_measures   {self.len_mm}')
        _p(f'{pad}len_micro_h    {self.len_uh}')
        _p("----------------------------------------------------")
        calc_fs = CS + self.len_mm + self.len_uh
        assert self.len_file == calc_fs

    @abstractmethod
    def _parse_macro_header(self):
        pass

    @abstractmethod
    def _create_csv_file(self):
        pass

    @abstractmethod
    def _parse_data_mm(self, mm, i, t):
        pass

    def _parse_data_micro_headers(self, uh, i):
        # 2B battery, 1B header index, 1B ECL, 4B epoch
        bat = int.from_bytes(uh[:i + 2], "big")
        idx = uh[i + 2]
        ecl = uh[i + 3]
        rt = int.from_bytes(uh[i + 4:i + 8], "big")
        _p(f"\n\tMICRO header \t|  detected")
        _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        _p("\theader index  \t|  0x{:02x} = {}".format(idx, idx))
        _p("\tpadding count \t|  0x{:02x} = {}".format(ecl, ecl))
        _p("\trelative time \t|  0x{:08x} = {}".format(rt, rt))
        self.d_uh[rt] = {"bat": bat, "idx": idx, "ecl": ecl}

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
        mm = bytes()
        uh = bytes()

        # n: number of chunks
        # iterate to build micro_headers and measurements byte arrays
        n = ceil(len(data) / CS)
        for i in range(0, CS * n, CS):
            mm += data[i+UHS:i+CS]
            uh += data[i:i+UHS]

        # -------------------------------
        # parse dictionary micro_headers
        # -------------------------------
        for i in range(0, UHS, len(uh)):
            self._parse_data_micro_headers(uh, i)

        # -----------------------------------
        # parse dictionary data measurements
        # -----------------------------------
        i = 0
        ta = 0
        while i < self.len_mm:
            i, t = self._parse_data_mm(mm, i, ta)
            ta += t

    def convert(self):
        self._load_file_bytes()
        self._get_file_length()
        self._parse_macro_header()
        self._parse_data()
        self._create_csv_file()
