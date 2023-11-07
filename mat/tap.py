import datetime
import os
from functools import lru_cache
from math import ceil

from dateutil.tz import tzlocal, tzutc

from mat.ascii85 import ascii85_to_num
from mat.pressure import Pressure
from mat.temperature import Temperature


class TAPConverterT:
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


class TAPConverterP:
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


PRF_FILE_CHUNK_SIZE = 256
LEN_CC_AREA = 5 * 40
LEN_MICRO_HEADER = 8
LEN_CONTEXT = 32
gcc_pra = 0
gcc_prb = 0
gcc_tma = 0
gcc_tmb = 0
gcc_tmc = 0
gcc_tmd = 0
gcc_tmr = 0
_fresh = True


def _seconds_between_two_time_str(a, b, fmt='%Y-%m-%dT%H:%M:%S.000'):
    dt_a = datetime.datetime.strptime(a, fmt)
    dt_b = datetime.datetime.strptime(b, fmt)
    return (dt_b - dt_a).total_seconds()


def _prf_build_indexes(lp, full_res=False):
    # lp: list of pressures
    # pb: profile built
    pb = list()
    for i in range(len(lp) - 1):
        if lp[i] < lp[i + 1]:
            c = 'd_'
        elif lp[i] > lp[i + 1]:
            c = 'a_'
        else:
            c = 'e_'
        if not full_res and pb and c in pb[-1]:
            pb.pop()
        pb.append('{}{}'.format(c, i + 1))
    # pb: ['d_2', 'e_4', 'd_8', 'a_10']
    return pb


def prf_describe(lp, lt) -> str:

    # ipb: indexes of profile built
    ipb = _prf_build_indexes(lp)

    # lp: list of pressures
    # lt: list of times
    txt = ''
    txt += '\nprofile textual description'
    txt += '\n---------------------------'
    vt = lt[0]
    txt += f'\n{lt[0]} -> start as depth {lp[0]}'
    last_vt = vt

    for p in ipb:
        # p: 'e_4'
        # grab index of interesting pressure
        i = int(p.split('_')[1])

        # grab value pressure
        vp = lp[i]

        # grab time of such index
        vt = lt[i]
        el = _seconds_between_two_time_str(last_vt, vt)

        # calculate time elapsed between two interesting points
        txt += '\n\t{:+d} seconds elapsed'.format(int(el))

        if 'd' in p:
            txt += f'\n{vt} -> falls to depth {vp}'
        elif 'a' in p:
            txt += f'\n{vt} -> rises to depth {vp}'
        else:
            txt += f'\n{vt} -> stays as depth {vp}'
        last_vt = vt

    # return the whole description
    txt += '\n'
    return txt


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


def _parse_data_mask(mask: bytes, ma_h: dict):
    # ma_h: macro_header
    # mask SSSSXXCC KKKKKKKK ---> must match firmware _mask_fill()
    # S = Sensors, X = RFU, CC = Interval Codes, K = Interval Skips
    sm = mask[0] & 0xf0
    cc = mask[0] & 0x03
    d_cc = {
        0: {'desc': 'sta', 'value': int(ma_h['spt'])},
        1: {'desc': 'out', 'value': int(ma_h['dro'])},
        2: {'desc': 'fast', 'value': int(ma_h['drf'])},
        3: {'desc': 'sub', 'value': int(ma_h['dru'])},
    }
    kk = mask[1]
    # todo --> parse sensors mask
    s_desc = 'sm = 0x{:02x}, '.format(sm)
    s_desc += f"{d_cc[cc]['desc'].upper()} = 0x{cc}, "
    s_desc += f"v -> {d_cc[cc]['value']}  * "
    s_desc += 'kk 0x{:02x}'.format(kk)
    v = d_cc[cc]['value']
    inc_s = v * (1 + kk)
    global _fresh
    inc_s = 0 if _fresh else inc_s
    _fresh = 0
    s_desc += f' = {inc_s} s'
    return s_desc, inc_s


def _parse_macro_header_start_time_to_seconds(s: str) -> int:
    # s: '231103190012' embedded in macro_header
    dt = datetime.datetime.strptime(s, "%y%m%d%H%M%S")
    # set dt as UTC since objects are 'naive' by default
    dt_utc = dt.replace(tzinfo=tzutc())
    dt_utc.astimezone(tzlocal())
    rv = dt_utc.timestamp()
    # rv: 1699038012
    return int(rv)


def _custom_time(b: bytes) -> str:
    s = ''
    for v in b:
        high = (v & 0xf0) >> 4
        low = (v & 0x0f) >> 0
        s += f'{high}{low}'
    return s


def _parse_chunk_type(b: bytes, ic) -> dict:

    i = 0
    if b[:3] == b"PRF":
        # ----------------------------------
        # macro header detected
        # da: dictionary macro-header
        # ----------------------------------
        da = {}
        print("\tMACRO header \t|  detected")
        print(f"\tchunk number \t|  #{ic}")
        i += 3
        file_version = b[i]
        print(f"\tfile version \t|  {file_version}")
        i += 1
        # 6 bytes of date YYMMDDHHMMSS
        v = b[i: i + 6]
        start_time = _custom_time(v)
        print("\tdatetime is   \t|  {}".format(start_time))
        i += 6
        # battery
        v = b[i: i + 2]
        bat = int.from_bytes(v, "big")
        print("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        i += 2
        hdr_idx = b[i]
        print(f"\theader index \t|  {hdr_idx}")
        i += 1
        cc_area = b[i: (i + LEN_CC_AREA)]
        assert b"00003" == cc_area[:5]
        print("\tcc_area \t\t|  detected")
        # nothing to return for macro-header
        n = len(cc_area)
        global gcc_tma
        global gcc_tmb
        global gcc_tmc
        global gcc_tmd
        global gcc_tmr
        global gcc_pra
        global gcc_prb
        gcc_tmr = ascii85_to_num(cc_area[10:15].decode())
        gcc_tma = ascii85_to_num(cc_area[15:20].decode())
        gcc_tmb = ascii85_to_num(cc_area[20:25].decode())
        gcc_tmc = ascii85_to_num(cc_area[25:30].decode())
        gcc_tmd = ascii85_to_num(cc_area[30:35].decode())
        gcc_pra = ascii85_to_num(cc_area[n - 10:n - 10 + 5].decode())
        gcc_prb = ascii85_to_num(cc_area[n - 5:n - 5 + 5].decode())
        pad = '\t\t\t\t\t   '
        print(f'{pad}tmr = {gcc_tmr}')
        print(f'{pad}tma = {gcc_tma}')
        print(f'{pad}tmb = {gcc_tmb}')
        print(f'{pad}tmc = {gcc_tmc}')
        print(f'{pad}tmd = {gcc_tmd}')
        print(f'{pad}pra = {gcc_pra}')
        print(f'{pad}prb = {gcc_prb}')

        # the last section of first header is the context
        n = PRF_FILE_CHUNK_SIZE - LEN_CONTEXT
        c = b[n: n + LEN_CONTEXT]
        print("\tcontext \t\t|  detected")
        rvn = c[0]
        pfm = c[1]
        spn = c[2]
        pma = c[3]
        spt = c[4:8].decode()
        dro = c[8:12].decode()
        dru = c[12:15].decode()
        drf = c[15:17].decode()
        dco = c[17:21].decode()
        dhu = c[21:24].decode()
        print(f'{pad}rvn = {rvn}')
        print(f'{pad}pfm = {pfm}')
        print(f'{pad}spn = {spn}')
        print(f'{pad}pma = {pma}')
        print(f'{pad}spt = {spt}')
        print(f'{pad}dro = {dro}')
        print(f'{pad}dru = {dru}')
        print(f'{pad}drf = {drf}')
        print(f'{pad}dco = {dco}')
        print(f'{pad}dhu = {dhu}')

        # fill the dict
        da['header_type'] = 'macro'
        da['file_version'] = file_version
        da['start_time'] = start_time
        da['battery_level'] = bat
        da['hdr_idx'] = hdr_idx
        da['gcc_tmr'] = gcc_tmr
        da['gcc_tma'] = gcc_tma
        da['gcc_tmb'] = gcc_tmb
        da['gcc_tmc'] = gcc_tmc
        da['gcc_tmd'] = gcc_tmd
        da['gcc_pra'] = gcc_pra
        da['gcc_prb'] = gcc_prb
        da['rvn'] = rvn
        da['pfm'] = pfm
        da['spn'] = spn
        da['pma'] = pma
        da['spt'] = spt
        da['dro'] = dro
        da['dru'] = dru
        da['drf'] = drf
        da['dco'] = dco
        da['dhu'] = dhu
        return da

    # ----------------------------------
    # micro header possible candidate
    # di: dictionary micro-header
    # ----------------------------------
    di = {}
    print('\n')
    print("\tmicro header \t|  detected")
    print(f"\tchunk number \t|  #{ic}")
    v = b[i: i + 2]
    bat = int.from_bytes(v, "big")
    print("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
    i += 2
    hdr_idx = b[i]
    print(f"\theader index \t|  {hdr_idx}")
    i += 1
    # this checks the ECL byte
    n_pad = b[i]
    print("\tpadding count \t|  0x{:02x} = {}".format(n_pad, n_pad))
    eff_len = PRF_FILE_CHUNK_SIZE - LEN_MICRO_HEADER - n_pad
    print(f"\tdata length \t|  {eff_len}")
    i += 1

    # ---------------------------------------------
    # data bytes are from LEN_MICRO_HEADER onwards
    # ---------------------------------------------
    data_bytes = b[LEN_MICRO_HEADER: LEN_MICRO_HEADER + eff_len]

    # fill the dict
    di['header_type'] = 'micro'
    di['battery_level'] = bat
    di['hdr_idx'] = hdr_idx
    di['data_bytes'] = data_bytes
    return di


def _data_to_csv_n_profile(d, csv_path: str, ma_h) -> dict:
    # ma_h: macro_header
    data = d['all_sensor_data']
    start_time = ma_h['start_time']
    epoch = _parse_macro_header_start_time_to_seconds(start_time)

    # todo ---> mask data length, calculate
    len_mask = 2
    len_data_sensor = 10
    len_sample = len_mask + len_data_sensor
    pad = '\t\t\t\t\t   '

    # ds: dictionary sensor data
    ds = dict()
    ds['sen_t'] = []
    ds['sen_p'] = []
    ds['sen_ax'] = []
    ds['sen_ay'] = []
    ds['sen_az'] = []
    ds['time'] = []

    # use the calibration coefficients to create objects
    tct = TAPConverterT(gcc_tma, gcc_tmb, gcc_tmc, gcc_tmd, gcc_tmr)
    tcp = TAPConverterP(gcc_pra, gcc_prb)

    # create header of csv_path
    f_csv = open(csv_path, 'w')
    cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),'\
           'Temperature (C),Pressure (dbar),Ax,Ay,Az\n'
    f_csv.write(cols)

    # get first time
    calc_epoch = epoch
    prev_t = ''
    ct = 0

    for _, i in enumerate(range(0, len(data), len_sample)):
        print(f'\tmeasure number \t|  #{_}')
        if _fresh:
            print(f'\tstart is fresh \t|  {_fresh}')

        # mask is meta-data
        m = data[i: i + 2]
        sm, inc_s = _parse_data_mask(m, ma_h)
        print('{}mk = 0x{:02x}{:02x}'.format(pad, m[0], m[1]))
        print(f'{pad}{sm}')

        # sensor is measurement data
        sen_t = data[i + 2: i + 4]
        sen_p = data[i + 4: i + 6]
        sen_ax = data[i + 6: i + 8]
        sen_ay = data[i + 8: i + 10]
        sen_az = data[i + 10: i + 12]
        vt = _decode_sensor_measurement('T', sen_t)
        vp = _decode_sensor_measurement('P', sen_p)
        vax = _decode_sensor_measurement('Ax', sen_ax)
        vay = _decode_sensor_measurement('Ay', sen_ay)
        vaz = _decode_sensor_measurement('Az', sen_az)
        ds['sen_t'].append(vt)
        ds['sen_p'].append(vp)
        ds['sen_ax'].append(vax)
        ds['sen_ay'].append(vay)
        ds['sen_az'].append(vaz)
        # print('{}T  = {}'.format(pad, vt))
        # print('{}P  = {}'.format(pad, vp))
        # print('{}Ax = {}'.format(pad, vax))
        # print('{}Ay = {}'.format(pad, vay))
        # print('{}Az = {}'.format(pad, vaz))
        # print('{}Tc = {}'.format(pad, tct.convert(vt)))
        # print('{}Pc = {}'.format(pad, tcp.convert(vp)))

        # convert to nicer values
        vt = '{:.02f}'.format(tct.convert(vt))
        vp = '{:.02f}'.format(tcp.convert(vp)[0])

        # CSV file and DESC file with LOCAL time...
        calc_epoch += inc_s
        # t = datetime.datetime.fromtimestamp(calc_epoch).isoformat() + ".000"
        # ... or with UTC time
        t = datetime.datetime.utcfromtimestamp(calc_epoch).isoformat() + ".000"
        ds['time'].append(t)

        # elapsed time
        prev_t = t if i == 0 else prev_t
        et = _seconds_between_two_time_str(prev_t, t)
        prev_t = t

        # cumulative time
        ct += et

        # format for columns
        s = f'{t},{et},{ct},{vt},{vp},{vax},{vay},{vaz}\n'

        # log to file
        f_csv.write(s)

    # close the file
    f_csv.close()

    # return built dictionary
    return ds


def _convert_lix_file(filepath):
    if not filepath.endswith('.lix'):
        print('error: this is not a lix file')
        assert False

    # load file input as bytes
    print("converting file", filepath)
    with open(filepath, "rb") as fi:
        # all of them
        bytes_file = fi.read()

    # calculate variables
    global _fresh
    _fresh = True
    sc = PRF_FILE_CHUNK_SIZE
    number_of_chunks = ceil(len(bytes_file) / sc)
    print("file length =", len(bytes_file))
    print("file chunks =", number_of_chunks)
    d = dict()
    d['all_sensor_data'] = bytes()

    # -----------------------
    # loop chunks in a file
    # -----------------------
    ma_h = dict()
    for ic in range(number_of_chunks):
        bytes_chunk = bytes_file[ic * sc: (ic * sc) + sc]
        hd = _parse_chunk_type(bytes_chunk, ic)
        if hd['header_type'] == 'macro':
            # store macro_header, will use later
            ma_h = hd
        if hd['header_type'] == 'micro':
            d['all_sensor_data'] += hd['data_bytes']

    # build csv file path
    csv_path = filepath[:-4] + '_TAP.csv'

    # create CSV file and description dictionary
    dpb = dict()
    dpb['sensor_data'] = _data_to_csv_n_profile(d, csv_path, ma_h)
    dpb['gcc_tma'] = gcc_tma
    dpb['gcc_tmb'] = gcc_tmb
    dpb['gcc_tmc'] = gcc_tmc
    dpb['gcc_tmd'] = gcc_tmd
    dpb['gcc_tmr'] = gcc_tmr
    dpb['gcc_pra'] = gcc_pra
    dpb['gcc_prb'] = gcc_prb

    # build profile description file using the dictionary
    lp = dpb['sensor_data']['sen_p']
    lt = dpb['sensor_data']['time']
    desc = prf_describe(lp, lt)
    desc_path = filepath[:-4] + '.txt'
    with open(desc_path, 'w') as ft:
        ft.write(desc)
    print(desc)


def convert_tap_file(path):
    try:
        _convert_lix_file(path)
        return 0, ''
    except (Exception, ) as ex:
        print('exception convert_lix_file {}'.format(ex))
        return 1, str(ex)


# -------
# tests
# -------
if __name__ == "__main__":
    # bread
    dl_fol = "/home/kaz/Downloads/dl_bil/D0-2E-AB-D9-29-48/"
    filename = ''
    path_lix_file = dl_fol + filename
    path_csv_file = path_lix_file[:-4] + '.csv'

    # tap 33
    # dl_fol = "/home/kaz/Downloads/dl_bil/D0-2E-AB-D9-32-6D/"
    # filename = "1111133_BIL_20231026_184118.lix"

    # set common name
    if os.path.exists('/tmp/bil_last_file_dl.txt'):
        with open('/tmp/bil_last_file_dl.txt', 'r') as f:
            path_lix_file = f.readline()
        print('replacing file being read with', path_lix_file)

    # just hardcoded
    # dl_fol = "/home/kaz/Downloads/dl_bil/11-22-33-44-55-66/"
    # filename = '2305733_BIL_20231102_134623.lix'
    # path_lix_file = dl_fol + filename

    convert_tap_file(path_lix_file)
