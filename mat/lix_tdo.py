from functools import lru_cache

from mat.ascii85 import ascii85_to_num
from mat.lix_abs import CS, LEN_LIX_FILE_CC_AREA, LEN_LIX_FILE_CONTEXT
from mat.lix_abs import ParserLixFile, _p, _mah_time_to_str, \
    _parse_macro_header_start_time_to_seconds, _decode_sensor_measurement, _mah_time_utc_epoch
import datetime

from mat.pressure import Pressure
from mat.temperature import Temperature

# flag debug
debug = 0


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
        # todo ---> unhardcode this
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
        psm = bb[i:i + 5].decode()

        # display all this info
        _p(f"\n\tMACRO header \t|  logger type {self.mah.file_type.decode()}")
        _p(f"\tfile version \t|  {self.mah.file_version}")
        self.mah.timestamp_str = _mah_time_to_str(self.mah.timestamp)

        utc_epoch = _mah_time_utc_epoch(self.mah.timestamp)

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
        _p(f'{pad}psm = {psm}')

    def _parse_data_mm(self, mm, i):
        _p(f"\n\tmeasurement #   |  {self.mm_i}")
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
            # build dictionary measurements
            self.d_mm[t] = mm[i:i + n]
        else:
            assert False

        # keep track of how many we decoded
        self.mm_i += 1

        # return current index of measurements' array
        return i + n

    def _create_csv_file(self):
        # use the calibration coefficients to create objects
        n = LEN_LIX_FILE_CC_AREA
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
        for k, v in self.d_mm.items():
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
