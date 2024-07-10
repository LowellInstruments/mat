import bisect
from functools import lru_cache

from mat.ascii85 import ascii85_to_num
from mat.lix_abs import CS, LEN_LIX_FILE_CC_AREA, LEN_LIX_FILE_CONTEXT, UHS, _raw_sensor_measurement
from mat.lix_abs import (ParserLixFile, _p, _mah_time_to_str,
                         _parse_macro_header_start_time_to_seconds,
                         _decode_sensor_measurement,
                         _mah_time_utc_epoch)
import datetime

from mat.pressure import Pressure
from mat.temperature import Temperature

# flag debug
debug = 0

LEN_BYTES_T = 2
LEN_BYTES_A = 6


def prf_compensate_pressure(rp, rt, prc, prd):
    # rp: raw Pressure ADC counts
    # rt: raw Temperature ADC counts
    # prc: temperature coefficient of pressure sensor = counts / °C
    # prd: reference temperature for pressure sensor = °C
    # cp: corrected Pressure ADC counts
    # ct: closest Temperature = °C

    # define lookup table, from -20°C to 50°C
    lut = [
       56765, 56316, 55850, 55369, 54872, 54359,
       53830, 53285, 52724, 52148, 51557, 50951,
       50331, 49697, 49048, 48387, 47714, 47028,
       46331, 45623, 44906, 44179, 43445, 42703,
       41954, 41199, 40440, 39676, 38909, 38140,
       37370, 36599, 35828, 35059, 34292, 33528,
       32768, 32012, 31261, 30517, 29780, 29049,
       28327, 27614, 26909, 26214, 25530, 24856,
       24192, 23541, 22900, 22272, 21655, 21051,
       20459, 19880, 19313, 18759, 18218, 17689,
       17174, 16670, 16180, 15702, 15236, 14782,
       14341, 13912, 13494, 13088, 12693
    ]

    # bisect needs a sorted list
    lut.reverse()

    # use vt to look up the closest temperature in degrees C, indexed T, i_t
    i_t = len(lut) - bisect.bisect(lut, rt)
    print(f'searching {rt} in lut -> i_t {i_t}')

    # use index of closest value (i_m) to get the T in °C, aka ct
    ct = i_t - 20
    print("ct =", ct)

    # corrected pressure ADC counts
    cp = rp - (prc * (ct - prd))
    print('\n')
    print(f"PRC = {prc} / PRD = {prd}")
    print(f"PRP = {rp}  / PCP = {cp}")
    print(f'PRP - PCP = {rp-cp}')

    return cp


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
        print('*', self.coefficients)
        print('*', raw_temperature, self.cnv.convert(raw_temperature))
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


class ParserLixTdoFile(ParserLixFile):
    def __init__(self, file_path, verbose=0):
        super().__init__(file_path)
        self.prc = 0
        self.prd = 0
        self.verbose = verbose

    def _parse_macro_header(self):
        self.mah.bytes = self.bb[:CS]
        bb = self.mah.bytes
        self.mah.file_type = bb[:3]
        self.mah.file_version = bb[3]
        self.mah.timestamp = bb[4:10]
        self.mah.battery = bb[10:12]
        self.mah.hdr_idx = bb[12]
        # HSA macro-header must match firmware hsa.h
        i_mah = 13
        self.mah.cc_area = bb[i_mah: i_mah + LEN_LIX_FILE_CC_AREA]
        # context
        i = CS - LEN_LIX_FILE_CONTEXT
        self.mah.context = bb[i:]
        gfv = bb[i:i+4]
        i += 4
        rvn = bb[i]
        i += 1
        pfm = bb[i]
        i += 1
        self.mah_context.spn = bb[i]
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
        self.mah_context.psm = bb[i:i + 5].decode()

        # display all this info
        _p(f"\n\tMACRO header \t|  logger type {self.mah.file_type.decode()}")
        _p(f"\tfile version \t|  {self.mah.file_version}")
        self.mah.timestamp_str = _mah_time_to_str(self.mah.timestamp)

        _p("\tdatetime is   \t|  {}".format(self.mah.timestamp_str))
        bat = int.from_bytes(self.mah.battery, "big")
        _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        _p(f"\theader index \t|  {self.mah.hdr_idx}")
        n = LEN_LIX_FILE_CC_AREA
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
        # PRC / PRD are not ascii85, also, we need them
        self.prc = float(self.mah.cc_area[n-10:n-5].decode()) / 100
        self.prd = float(self.mah.cc_area[n-5:].decode()) / 100
        _p(f'{pad}prc = {self.prc}')
        _p(f'{pad}prd = {self.prd}')
        _p("\tcontext \t\t|  detected")
        _p(f'{pad}gfv = {gfv}')
        _p(f'{pad}rvn = {rvn}')
        _p(f'{pad}pfm = {pfm}')
        _p(f'{pad}spn = {self.mah_context.spn}')
        _p(f'{pad}pma = {pma}')
        _p(f'{pad}spt = {spt}')
        _p(f'{pad}dro = {dro}')
        _p(f'{pad}dru = {dru}')
        _p(f'{pad}drf = {drf}')
        _p(f'{pad}dco = {dco}')
        _p(f'{pad}dhu = {dhu}')
        _p(f'{pad}psm = {self.mah_context.psm}')

    # def _parse_data_mm_with_sensor_mask(self, mm, i, ta):
    #     # mm: all measurement bytes, no micro_headers but yes masks
    #     # i: byte index in big array of measurements
    #     _p(f"\n\tmeasurement \t|  #{self.mm_i}")
    #
    #     # to calculate index bytes
    #     j = i
    #     k = i
    #
    #     # extract sample mask flags of first byte
    #     f_sm = mm[i] & 0x80
    #     f_te = mm[i] & 0x40
    #
    #     # calculate sensor mask and time
    #     if f_sm == 0 and f_te == 0:
    #         s = 'ts'
    #         self.sm = self.mah_context.psm
    #         if self.sm == '00000':
    #             self.sm = 0x13
    #         t = 0x3F & mm[i]
    #         i += 1
    #     elif f_sm == 0 and f_te == 1:
    #         s = 'te'
    #         self.sm = self.mah_context.psm
    #         if self.sm == '00000':
    #             self.sm = 0x13
    #         t = ((0x3F & mm[i]) << 8) + mm[i+1]
    #         i += 2
    #     elif f_sm == 1 and f_te == 0:
    #         s = 'sm ts'
    #         self.sm = mm[i] & 0x3F
    #         t = 0x3F & mm[i+1]
    #         i += 2
    #     else:
    #         s = 'sm te'
    #         self.sm = mm[i] & 0x3F
    #         t = ((0x3F & mm[i+1]) << 8) + mm[i+2]
    #         i += 3
    #
    #     # show mask from beginning
    #     _p(f'\tlen. mask\t\t|  {i-k} -> {s}')
    #     _p(f'\\flags mask \t|  f_sm = {f_sm}, f_te = {f_te}')
    #     if f_sm:
    #         _p('\t\t\t\t\t|  sm = {0x{:02x}'.format(self.sm))
    #     if f_te == 0:
    #         _p('\t\t\t\t\t|  ts = 0x{:02x}'.format(t))
    #     else:
    #         _p('\t\t\t\t\t|  te = 0x{:04x}'.format(t))
    #
    #     # sample mask, get sample length
    #     _d_sm = {
    #         0x11: 0,
    #         0x13: 1,
    #         0x15: 2,
    #         0x17: 4,
    #         0x19: 8
    #     }
    #     np = 2 * (_d_sm[self.sm])
    #     n = np + LEN_BYTES_T + LEN_BYTES_A
    #     _p(f"\tlen. sensors\t|  {n}")
    #
    #     # build dictionary measurements, with sensor mask
    #     self.d_mm[ta + t] = (mm[i:i + n], self.sm)
    #
    #     # keep track of how many measurements we decoded
    #     self.mm_i += 1
    #
    #     # display bytes involved
    #     # K can probably be simplified here
    #     _p('\t #P samples\t\t|  {}'.format(_d_sm[self.sm]))
    #     _p(f'\tindex bytes \t|  {j}:{j+n+i-k} ({n+i-k})')
    #
    #     c = mm[j:j+n+i-k]
    #     for a, b in enumerate(c):
    #         print(a, '0x{:02x}'.format(b))
    #
    #     # return current index of measurements' array
    #     return i + n, t

    def _parse_data_mm(self, mm, i, ta):

        # mm: all measurement bytes, no micro_headers but yes masks
        _p(f"\n\tmeasurement \t|  #{self.mm_i}")

        # get current byte in big array of measurements and time mask
        j = i
        f_te = mm[i] & 0x40
        if f_te == 0:
            t = 0x3F & mm[i]
            i += 1
            _p('\tlen. mask\t\t|  1 -> ts = 0x{:02x} = {}'.format(t, t))
        else:
            t = ((0x3F & mm[i]) << 8) + mm[i+1]
            i += 2
            _p('\tlen. mask\t\t|  2 -> te = 0x{:04x} = {}'.format(t, t))

        # calculate measurement number of bytes
        np = 2 * self.mah_context.spn
        n = np + LEN_BYTES_T + LEN_BYTES_A
        _p(f"\tlen. sensors\t|  {n}")

        # build dictionary measurements, self.sm is for future features
        self.d_mm[ta + t] = (mm[i:i + n], self.sm)

        # keep track of how many measurements we decoded
        self.mm_i += 1

        # display postions of bytes involved
        _p(f'\tindex bytes \t|  {j}:{n+i} ({n+i-j})')

        # debug this measurement
        # c = mm[j:n+i]
        # for a, b in enumerate(c):
        #     print(a, '0x{:02x}'.format(b))

        # return current index of measurements' array
        return i + n, t

    def _create_csv_file(self):
        # use the calibration coefficients to create objects
        np = LEN_LIX_FILE_CC_AREA
        tmr = ascii85_to_num(self.mah.cc_area[10:15].decode())
        tma = ascii85_to_num(self.mah.cc_area[15:20].decode())
        tmb = ascii85_to_num(self.mah.cc_area[20:25].decode())
        tmc = ascii85_to_num(self.mah.cc_area[25:30].decode())
        tmd = ascii85_to_num(self.mah.cc_area[30:35].decode())
        pra = ascii85_to_num(self.mah.cc_area[np-20:np-15].decode())
        prb = ascii85_to_num(self.mah.cc_area[np-15:np-10].decode())
        lct = LixFileConverterT(tma, tmb, tmc, tmd, tmr)
        lcp = LixFileConverterP(pra, prb)

        # ---------------
        # csv file header
        # ---------------
        csv_path = (self.file_path[:-4] + '_TDO.csv')
        f_csv = open(csv_path, 'w')
        cols = 'ISO 8601 Time,' \
               'Temperature (C),Pressure (dbar),Ax,Ay,Az\n'
        if self.verbose:
            cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),' \
                   'raw ADC Temp,raw ADC Pressure,' \
                   'Temperature (C),Pressure (dbar),Compensated ADC Pressure,' \
                   'Compensated Pressure (dbar),Ax,Ay,Az\n'
        f_csv.write(cols)

        # get first time
        epoch = _parse_macro_header_start_time_to_seconds(self.mah.timestamp_str)
        last_ct = 0

        # debug all measurements
        # print('\ndictionary measurements')
        # print(self.d_mm)

        # self.d_mm: dictionary {cumulative_time: (sensor_data, sensor_mask)}
        for ct, v_sm in self.d_mm.items():
            v, sm = v_sm

            # needed arrays for pressure
            rpe, cpe = [], []

            # temperature in ADC counts
            rt = _raw_sensor_measurement(v[0:2])

            # temperature floating point format
            vt = '{:06.3f}'.format(float(lct.convert(rt)))

            # pressure: up to 'np' samples
            np = int((len(v) - (LEN_BYTES_T + LEN_BYTES_A)) / 2)
            for i in range(np):
                # rp: raw ADC pressure
                rp = _raw_sensor_measurement(v[2+(i*2):(2+(i*2))+2])
                rpe.append(rp)

                # cp: compensated ADC pressure, uses PRC / PRD
                cp = prf_compensate_pressure(rp, rt, self.prc, self.prd)
                cpe.append(cp)

            # accelerometer
            vax = _decode_sensor_measurement('Ax', v[-6:-4])
            vay = _decode_sensor_measurement('Ay', v[-4:-2])
            vaz = _decode_sensor_measurement('Az', v[-2:])

            # CSV file writing
            for i in range(np):
                # convert raw pressure to decibar using PRA / PRB
                vp = '{:06.3f}'.format(lcp.convert(rpe[i])[0])
                # convert compensated pressure to decibar using PRA / PRB
                kp = '{:06.3f}'.format(lcp.convert(cpe[i])[0])

                # timestamp
                sub_t = '{:.3f}'.format(i / np)
                # sub_t: 'X.250' -> '250'
                sub_t = sub_t[-3:]
                t = datetime.datetime.utcfromtimestamp(epoch + ct).isoformat() + f'.{sub_t}Z'

                # elapsed and cumulative time
                et = ct - last_ct
                last_ct = ct
                s = f'{t},{vt},{vp},{vax},{vay},{vaz}\n'
                if self.verbose:
                    s = f'{t},{et},{ct},{rt},{rpe[i]},{vt},{vp},{cpe[i]},'\
                        f'{kp},{vax},{vay},{vaz}\n'
                f_csv.write(s)

        # close the file
        f_csv.close()

        # return name of CSV file
        return csv_path


if __name__ == '__main__':
    rp = 11056
    rt = 29706
    prc = 1
    prd = 1
    v = prf_compensate_pressure(rp, rt, prc, prd)
    print(v)
