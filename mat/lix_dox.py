from functools import lru_cache

from mat.ascii85 import ascii85_to_num
from mat.lix import ParserLixFile, CS, LEN_CC_AREA, LEN_CONTEXT, _p, _custom_time, \
    _parse_macro_header_start_time_to_seconds, _decode_sensor_measurement
import datetime

from mat.pressure import Pressure
from mat.temperature import Temperature

# flag debug
debug = 0


class ParserLixDoxFile(ParserLixFile):
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
        # DOX loggers do not use HSA much
        i_mah = 13
        self.mah.cc_area = bb[i_mah: i_mah + LEN_CC_AREA]
        # DOX loggers do not use context much
        i = CS - LEN_CONTEXT
        self.mah.context = bb[i:]
        print(self.mah.context)
        spt = bb[8:13].decode()

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
        _p(f"\tSPT period   \t|  {spt}")

    def _parse_data_measurement(self, mm, i):
        # DOX loggers they don't use mask
        _p(f"\n\tmeasurement #   |  {self.measurement_number}")
        if self.mah.file_type.decode() == 'DO1':
            n = 6
            # build dictionary
            # self.d_measurements[t] = mm[i:i+n]
        elif self.mah.file_type.decode() == 'DO2':
            # these do water too
            n = 8
        else:
            assert False

        # keep track of how many we decoded
        self.measurement_number += 1

        # return current index of measurements' array
        return i + n

    def _create_csv_file(self):
        pass
        # # use the calibration coefficients to create objects
        # n = LEN_CC_AREA
        # tmr = ascii85_to_num(self.mah.cc_area[10:15].decode())
        # tma = ascii85_to_num(self.mah.cc_area[15:20].decode())
        # tmb = ascii85_to_num(self.mah.cc_area[20:25].decode())
        # tmc = ascii85_to_num(self.mah.cc_area[25:30].decode())
        # tmd = ascii85_to_num(self.mah.cc_area[30:35].decode())
        # pra = ascii85_to_num(self.mah.cc_area[n-20:n-15].decode())
        # prb = ascii85_to_num(self.mah.cc_area[n-15:n-10].decode())
        # lct = LixFileConverterT(tma, tmb, tmc, tmd, tmr)
        # lcp = LixFileConverterP(pra, prb)
        #
        # # ---------------
        # # csv file header
        # # ---------------
        # csv_path = (self.file_path[:-4] +
        #             '_' + self.mah.file_type.decode() + '.csv')
        # f_csv = open(csv_path, 'w')
        # cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),' \
        #        'Temperature (C),Pressure (dbar),Ax,Ay,Az\n'
        # f_csv.write(cols)
        #
        # # get first time
        # epoch = _parse_macro_header_start_time_to_seconds(self.mah.timestamp_str)
        # calc_epoch = epoch
        # ct = 0
        # for k, v in self.d_measurements.items():
        #     # {t}: {sensor_data}
        #     vt = _decode_sensor_measurement('T', v[0:2])
        #     vp = _decode_sensor_measurement('P', v[2:4])
        #     vax = _decode_sensor_measurement('Ax', v[4:6])
        #     vay = _decode_sensor_measurement('Ay', v[6:8])
        #     vaz = _decode_sensor_measurement('Az', v[8:10])
        #     vt = '{:.02f}'.format(lct.convert(vt))
        #     vp = '{:.02f}'.format(lcp.convert(vp)[0])
        #
        #     # CSV file and DESC file with LOCAL time...
        #     calc_epoch += k
        #     # UTC time, o/wise use fromtimestamp()
        #     t = datetime.datetime.utcfromtimestamp(calc_epoch).isoformat() + ".000"
        #
        #     # elapsed and cumulative time
        #     # todo ---> check this works with more than 3 samples
        #     et = calc_epoch - epoch
        #     ct += et
        #
        #     # log to file
        #     s = f'{t},{et},{ct},{vt},{vp},{vax},{vay},{vaz}\n'
        #     f_csv.write(s)
        #     print(s)
        #
        # # close the file
        # f_csv.close()


if __name__ == '__main__':
    # p = '/home/kaz/Downloads/dl_bil/9999999_BIL_20240122_195627.lix'
    p = '/home/kaz/Downloads/dl_bil/60-77-71-22-CA-6D/1111111_tst_20240131_202758.lix'
    plf = ParserLixDoxFile(p)
    plf.convert_lix_file()
