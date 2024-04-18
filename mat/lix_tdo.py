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


class ParserLixTdoFile(ParserLixFile):
    def __init__(self, file_path):
        super().__init__(file_path)

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
        self.mah.cf_psm = bb[i:i + 5].decode()

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
        _p(f'{pad}psm = {self.mah.cf_psm}')

    def _parse_data_mm(self, mm, i, ta):
        # mm: all measurement bytes, no micro_headers but yes masks
        # i: byte index in big array of measurements
        _p(f"\n\tmeasurement \t|  #{self.mm_i}")

        # to calculate index bytes
        j = i
        k = i

        # extract sample mask flags of first byte
        f_sm = mm[i] & 0x80
        f_te = mm[i] & 0x40

        # calculate sensor mask and time
        if f_sm == 0 and f_te == 0:
            s = 'ts'
            self.sm = self.mah.cf_psm
            if self.sm == '00000':
                self.sm = 0x13
            t = 0x3F & mm[i]
            i += 1
        elif f_sm == 0 and f_te == 1:
            s = 'te'
            self.sm = self.mah.cf_psm
            if self.sm == '00000':
                self.sm = 0x13
            t = ((0x3F & mm[i]) << 8) + mm[i+1]
            i += 2
        elif f_sm == 1 and f_te == 0:
            s = 'sm ts'
            self.sm = mm[i] & 0x3F
            t = 0x3F & mm[i+1]
            i += 2
        else:
            s = 'sm te'
            self.sm = mm[i] & 0x3F
            t = ((0x3F & mm[i+1]) << 8) + mm[i+2]
            i += 3

        # show mask from beginning
        _p(f'\tlen. mask\t\t|  {i-k} -> {s}')
        _p(f'\\flags mask \t|  f_sm = {f_sm}, f_te = {f_te}')
        if f_sm:
            _p('\t\t\t\t\t|  sm = {0x{:02x}'.format(self.sm))
        if f_te == 0:
            _p('\t\t\t\t\t|  ts = 0x{:02x}'.format(t))
        else:
            _p('\t\t\t\t\t|  te = 0x{:04x}'.format(t))

        # sample mask, get sample length
        _d_sm = {
            0x11: 0,
            0x13: 1,
            0x15: 2,
            0x17: 4,
            0x19: 8
        }
        np = 2 * (_d_sm[self.sm])
        n = np + LEN_BYTES_T + LEN_BYTES_A
        _p(f"\tlen. sensors\t|  {n}")

        # build dictionary measurements, with sensor mask
        self.d_mm[ta + t] = (mm[i:i + n], self.sm)

        # keep track of how many measurements we decoded
        self.mm_i += 1

        # display bytes involved
        # todo ---> K can probably be simplified here
        _p('\t #P samples\t\t|  {}'.format(_d_sm[self.sm]))
        _p(f'\tindex bytes \t|  {j}:{j+n+i-k} ({n+i-k})')

        c = mm[j:j+n+i-k]
        for a, b in enumerate(c):
            print(a, '0x{:02x}'.format(b))

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
        cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),' \
               'raw ADC Temp,raw ADC Pressure,' \
               'Temperature (C),Pressure (dbar),Ax,Ay,Az\n'
        f_csv.write(cols)

        # get first time
        epoch = _parse_macro_header_start_time_to_seconds(self.mah.timestamp_str)
        last_ct = 0

        # debug
        print('\ndictionary measurements')
        print(self.d_mm)

        # ct: cumulative time
        for ct, v_sm in self.d_mm.items():
            # self.d_mm is a dictionary {t: (sensor_data, sensor_mask)}
            v, sm = v_sm
            vt = _decode_sensor_measurement('T', v[0:2])
            rt = _raw_sensor_measurement(v[0:2])
            # get length of Pressure data
            np = int((len(v) - (LEN_BYTES_T + LEN_BYTES_A)) / 2)
            vpe, rpe = [], []
            for i in range(np):
                vp = _decode_sensor_measurement('P', v[2+(i*2):(2+(i*2))+2])
                rp = _raw_sensor_measurement(v[2+(i*2):(2+(i*2))+2])
                vpe.append(vp)
                rpe.append(rp)
            vax = _decode_sensor_measurement('Ax', v[-6:-4])
            vay = _decode_sensor_measurement('Ay', v[-4:-2])
            vaz = _decode_sensor_measurement('Az', v[-2:])

            # CSV file has UTC time
            vt = '{:06.3f}'.format(float(lct.convert(vt)))
            for i in range(np):
                sub_t = '{:.3f}'.format(i / np)
                t = (datetime.datetime.utcfromtimestamp(epoch + ct).isoformat() +
                     "." + sub_t + 'Z')
                vp = '{:06.3f}'.format(lcp.convert(vpe[i])[0])
                rp = rpe[i]
                et = ct - last_ct
                last_ct = ct
                # log to file
                s = f'{t},{et},{ct},{rt},{rp},{vt},{vp},{vax},{vay},{vaz}\n'
                f_csv.write(s)

        # close the file
        f_csv.close()

        # return name of CSV file
        return csv_path


