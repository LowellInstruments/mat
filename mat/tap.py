import datetime
import os
import sys
import humanize
from functools import lru_cache
from math import ceil, floor
from dateutil.tz import tzlocal, tzutc
from humanize import naturaldelta

from mat.ascii85 import ascii85_to_num
from mat.pressure import Pressure
from mat.temperature import Temperature


g_header_index = 1
g_verbose = True


# ---------------------------------------------------------------
# the LIX file format, chunks are 256 bytes long
# chunk #0 is just a macro-header
#     [    0 .. 2] = file descriptor = "PRF"
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
#         [0 .. 2] = battery measurement
#         [     3] = header index
#         [     4] = effective chunk length
#         [5 .. 7] = seconds since we started
# ---------------------------------------------------------------


def _p(s, **kwargs):
    if g_verbose:
        print(s, **kwargs)


def _show_bytes(bb: bytes, length: int):
    for i, b in enumerate(bb):
        if i % length == 0:
            _p('')
        _p('{:02x} '.format(b), end='')
    _p('')


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
LEN_CC_AREA = 29 * 5
LEN_MICRO_HEADER = 8
LEN_CONTEXT = 36
gcc_pra = 0
gcc_prb = 0
gcc_prc = 0
gcc_prd = 0
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

    # ----------------------------------------
    # detect TAP logger LIX file macro-header
    # ----------------------------------------
    if ic == 0 and b[:3] == b"PRF":
        # ----------------------------------
        # macro header detected
        # da: dictionary macro-header
        # ----------------------------------
        da = {}
        _p("\tMACRO header \t|  logger type TAP")
        i += 3
        file_version = b[i]
        _p(f"\tfile version \t|  {file_version}")
        i += 1
        # 6 bytes of date YYMMDDHHMMSS
        v = b[i: i + 6]
        start_time = _custom_time(v)
        _p("\tdatetime is   \t|  {}".format(start_time))
        i += 6
        # battery
        v = b[i: i + 2]
        bat = int.from_bytes(v, "big")
        _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        i += 2
        hdr_idx = b[i]
        _p(f"\theader index \t|  {hdr_idx}")
        i += 1
        cc_area = b[i: (i + LEN_CC_AREA)]
        if b"00003" != cc_area[:5]:
            return {}
        _p("\tcc_area \t\t|  detected")

        # -------------------------------
        # HSA embedded in macro-header
        # must match firmware hsa.h
        # -------------------------------
        n = len(cc_area)
        global gcc_tma
        global gcc_tmb
        global gcc_tmc
        global gcc_tmd
        global gcc_tmr
        global gcc_pra
        global gcc_prb
        global gcc_prc
        global gcc_prd
        gcc_tmr = ascii85_to_num(cc_area[10:15].decode())
        gcc_tma = ascii85_to_num(cc_area[15:20].decode())
        gcc_tmb = ascii85_to_num(cc_area[20:25].decode())
        gcc_tmc = ascii85_to_num(cc_area[25:30].decode())
        gcc_tmd = ascii85_to_num(cc_area[30:35].decode())
        gcc_pra = ascii85_to_num(cc_area[n - 20:n - 15].decode())
        gcc_prb = ascii85_to_num(cc_area[n - 15:n - 10].decode())
        # gcc_prc = ascii85_to_num(cc_area[n - 10:n - 5].decode())
        # gcc_prd = ascii85_to_num(cc_area[n - 5:].decode())
        pad = '\t\t\t\t\t   '
        _p(f'{pad}tmr = {gcc_tmr}')
        _p(f'{pad}tma = {gcc_tma}')
        _p(f'{pad}tmb = {gcc_tmb}')
        _p(f'{pad}tmc = {gcc_tmc}')
        _p(f'{pad}tmd = {gcc_tmd}')
        _p(f'{pad}pra = {gcc_pra}')
        _p(f'{pad}prb = {gcc_prb}')
        # _p(f'{pad}prc = {gcc_prc}')
        # _p(f'{pad}prd = {gcc_prd}')

        # the last section of first header is the context
        n = PRF_FILE_CHUNK_SIZE - LEN_CONTEXT
        c = b[n: n + LEN_CONTEXT]
        _p("\tcontext \t\t|  detected")
        # these lengths must match the firmware limits for variables
        i = 0
        gfv = c[i:i+4]
        i += 4
        rvn = c[i]
        i += 1
        pfm = c[i]
        i += 1
        spn = c[i]
        i += 1
        pma = c[i]
        i += 1
        spt = c[i:i+4].decode()
        i += 4
        dro = c[i:i+4].decode()
        i += 4
        dru = c[i:i+3].decode()
        i += 3
        drf = c[i:i+2].decode()
        i += 2
        dco = c[i:i+4].decode()
        i += 4
        dhu = c[i:i+3].decode()
        i += 3
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

        # offset
        _p(f"\toffset \t\t\t|  [{ic * 256} : {(ic * 256) + 256}]")

        # fill the dict
        da['header_type'] = 'macro'
        da['logger_type'] = b[:3].decode().lower()
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
        # da['gcc_prc'] = gcc_prc
        # da['gcc_prd'] = gcc_prd
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

    # ----------------------------------------
    # detect TAP logger DO2 file macro-header
    # ----------------------------------------
    elif ic == 0 and b[:3] == b"DO2":
        # todo: do this for DO2 loggers
        da = {}
        return da

    # ----------------------------------
    # MICRO header possible candidate
    # di: dictionary micro-header
    # ----------------------------------
    di = {}
    _p('\n')
    _p(f"\tmicro header \t|  detected, length {LEN_MICRO_HEADER}")
    v = b[i: i + 2]
    bat = int.from_bytes(v, "big")
    _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
    i += 2

    # check header index
    hdr_idx = b[i]
    global g_header_index
    if g_header_index % 256 != hdr_idx:
        e = f'warning: g_header_index {g_header_index} does not match hdr_idx {hdr_idx}'
        _p(e)
    g_header_index += 1
    _p("\theader index \t|  0x{:02x} = {}".format(hdr_idx, hdr_idx))
    i += 1

    # check ECL byte
    n_pad = b[i]
    _p("\tpadding count \t|  0x{:02x} = {}".format(n_pad, n_pad))
    eff_len = PRF_FILE_CHUNK_SIZE - LEN_MICRO_HEADER - n_pad
    _p(f"\tdata length \t|  {eff_len}")
    i += 1
    _p(f"\toffset \t\t\t|  [{ic * 256} : {(ic * 256) + 256}]")

    # ---------------------------------------------
    # data bytes are from LEN_MICRO_HEADER onwards
    # ---------------------------------------------
    data_bytes = b[LEN_MICRO_HEADER: LEN_MICRO_HEADER + eff_len]

    _show_bytes(data_bytes, 12)

    # fill the dict
    di['header_type'] = 'micro'
    di['battery_level'] = bat
    di['hdr_idx'] = hdr_idx
    di['data_bytes'] = data_bytes
    return di


def _parse_file_lix(filepath):

    # load file input as bytes
    _p(f"converting file {filepath}")
    with open(filepath, "rb") as fi:
        # all of them
        bytes_file = fi.read()

    # calculate variables
    global _fresh
    _fresh = True
    sc = PRF_FILE_CHUNK_SIZE
    number_of_chunks = ceil(len(bytes_file) / sc)
    _p(f"file length = {len(bytes_file)}")
    _p(f"file chunks = {number_of_chunks}")
    d = dict()
    d['all_sensor_data'] = bytes()

    # -----------------------
    # loop chunks in a file
    # -----------------------
    for ic in range(number_of_chunks):
        bytes_chunk = bytes_file[ic * sc: (ic * sc) + sc]
        # ---------------------------------
        # parse chunk type: macro or micro
        # ---------------------------------
        _ct = _parse_chunk_type(bytes_chunk, ic)
        if _ct == {}:
            return {}
        if _ct['header_type'] == 'macro':
            d['macro_header'] = _ct
            _show_bytes(bytes_chunk, 8)
        if _ct['header_type'] == 'micro':
            d['all_sensor_data'] += _ct['data_bytes']

    # dictionary with bot header info and all BINARY data
    return d


def _create_file_csv(d, lix_path):

    # ma_h: macro_header
    ma_h = d['macro_header']
    data = d['all_sensor_data']
    start_time = ma_h['start_time']
    epoch = _parse_macro_header_start_time_to_seconds(start_time)

    # todo ---> mask data length, calculate depending on sensor length
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
    csv_path = lix_path[:-4] + '_TAP.csv'
    f_csv = open(csv_path, 'w')
    cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),' \
           'Temperature (C),Pressure (dbar),Ax,Ay,Az\n'
    f_csv.write(cols)

    # get first time
    calc_epoch = epoch
    prev_t = ''
    ct = 0

    for _, i in enumerate(range(0, len(data), len_sample)):
        _p(f'\tmeasure number \t|  #{_}')
        # i_ch = floor((_ * 12) / 248) + 1
        # # + 1 for macro_header
        # _p(f'\tchunk  in file \t|  #{i_ch}')
        # # _p(f'\tchunk  contains\t|  {i_ch * 256} to {(i_ch + 1) * 256}')
        # o_ch = floor((_ * 12) % 248) + 8
        # _p(f'\toffset in chunk\t|  {o_ch}')

        if _fresh:
            _p(f'\tstart is fresh \t|  {_fresh}')

        # mask is meta-data
        m = data[i: i + 2]
        sm, inc_s = _parse_data_mask(m, ma_h)
        _p('{}mk = 0x{:02x}{:02x}'.format(pad, m[0], m[1]))

        if m[0] == 0x92 and m[1] != 0x00:
            _p('error mask: moving logger cannot have skips')

        _p(f'{pad}{sm}')

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
        # _p('{}T  = {}'.format(pad, vt))
        # _p('{}P  = {}'.format(pad, vp))
        # _p('{}Ax = {}'.format(pad, vax))
        # _p('{}Ay = {}'.format(pad, vay))
        # _p('{}Az = {}'.format(pad, vaz))
        # _p('{}Tc = {}'.format(pad, tct.convert(vt)))
        # _p('{}Pc = {}'.format(pad, tcp.convert(vp)))

        # -------------------------------------------------
        # use MAT library to get friendlier values for CSV
        # -------------------------------------------------
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


def _create_file_des(d, csv_path):
    lp = d['sen_p']
    lt = d['time']
    desc = prf_describe(lp, lt)
    desc_path = csv_path[:-4] + '.txt'
    with open(desc_path, 'w') as ft:
        ft.write(desc)


def _get_logger_type_from_lix_file(d_lix):
    """
    converts LIX file label to logger type
    :param d_lix: dictionary containing LIX header and data
    :return:
    """
    t = d_lix['macro_header']['logger_type']
    if t == "prf":
        return "TAP"
    if t == "do2":
        return "DO2"


def convert_tap_file(path, verbose=True):
    """
    function called when wanting to convert a LIX file
    for example, DDH project calls this function
    in turns, this function calls:
        - _parse_file_lix() -> builds dict using file chunks
        - _create_file_csv() -> uses dict to create CSV file
    :param path: where is the LIX file
    :param verbose: show more info about the process
    :return:
    """
    global g_header_index
    g_header_index = 1
    global g_verbose
    g_verbose = verbose

    try:
        # d_lix: {'macro_header': bytes_macro_header,
        #         'all_file_data': bytes_file_data}
        d_lix = _parse_file_lix(path)
        if not d_lix:
            return 1, f'error: converting file {path}'

        lt = _get_logger_type_from_lix_file(d_lix)
        if not lt:
            return 1, f'error: converting file {path}, no logger type'

        # parse file according its logger type
        if lt == "TAP":
            # d_csv: {time1: data, time2: data, ....}
            d_csv = _create_file_csv(d_lix, path)
            _create_file_des(d_csv, path)
        elif lt == "DO2":
            pass

        # went well
        return 0, ''

    except (Exception, ) as ex:
        _p('exception convert_lix_file {}'.format(ex))
        return 1, str(ex)


# -------
# tests
# -------
if __name__ == "__main__":
    # bread
    dl_fol = "/home/kaz/Downloads/dl_bil/D0-2E-AB-D9-32-6D/"
    filename = '2311732_BIL_20231201_161342.lix'
    path_lix_file = dl_fol + filename
    path_csv_file = path_lix_file[:-4] + '.csv'

    # set common name
    # if os.path.exists('/tmp/bil_last_file_dl.txt'):
    #     with open('/tmp/bil_last_file_dl.txt', 'r') as f:
    #         path_lix_file = f.readline()
    #     _p(f'replacing file being read with {path_lix_file}')

    convert_tap_file(path_lix_file)


def prf_detection_steal(lp, lt) -> str:

    # lp: list of pressures
    # lt: list of times
    txt = ''
    txt += '\nprofile hauling detection'
    txt += '\n---------------------------'
    vt = lt[0]
    txt += f'\n{lt[0]} -> start as depth {lp[0]}'

    # out, sub
    state = None
    threshold = 10
    time_out = None

    j = 0

    for i, vp in enumerate(lp):

        # grab values of time
        vt = lt[i]

        # state FSM
        prev_state = state
        state = 'out' if int(float(vp)) < threshold else 'sub'
        if state == 'out' and prev_state == 'sub':
            time_out = vt
        if state == 'sub' and prev_state == 'out':
            time_sub = vt
            el = _seconds_between_two_time_str(time_out, time_sub)
            txt += f'\nhaul detected, duration: {naturaldelta(el)}'
            txt += f'\n\t- time start: {time_out}'
            txt += f'\n\t- time end:   {time_sub}'
            time_out = None
            j += 1

    # return the whole description
    txt += '\n'
    return txt


# if __name__ == "__main__":
#     dl_fol = "/home/kaz/Downloads/60-77-71-22-ca-21/"
#     filename = dl_fol + "2311733_BIL_20231201_191733_TAP.csv"
#
#     _lp, _lt = [], []
#     with open(filename) as f:
#         ll = f.readlines()
#         ll = ll[1:]
#         for i in ll:
#             _lt.append(i.split(',')[0])
#             _lp.append(i.split(',')[4])
#
#     desc = prf_detection_steal(_lp, _lt)
#     print(desc)
