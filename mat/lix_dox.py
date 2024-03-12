from datetime import datetime

from mat.lix_abs import CS, LEN_LIX_FILE_CC_AREA, LEN_LIX_FILE_CONTEXT
from mat.lix_abs import (ParserLixFile,
                         _p, _mah_time_to_str,
                         _mah_time_utc_epoch)

# flag debug
debug = 0


def do16_to_float(d):
    # d: 0x8003
    sign = bool(d & 0x8000)
    v = d & 0x7FFF
    f = v * 0.01
    if sign:
        f *= -1
    return f


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
        self.mah.cc_area = bb[i_mah: i_mah + LEN_LIX_FILE_CC_AREA]
        # DOX loggers do not use context much
        i = CS - LEN_LIX_FILE_CONTEXT
        self.mah_context.bytes = bb[i:]
        self.mah_context.spt = self.mah_context.bytes[8:13].decode()

        # display macro_header DOX info
        _p(f"\n\tMACRO header \t|  logger type {self.mah.file_type.decode()}")
        _p(f"\tfile flavor    \t|  {self.mah.file_version}")
        self.mah.timestamp_str = _mah_time_to_str(self.mah.timestamp)
        self.mah.timestamp_epoch = int(_mah_time_utc_epoch(self.mah.timestamp))
        _p("\tdatetime is   \t|  {}".format(self.mah.timestamp_str))
        bat = int.from_bytes(self.mah.battery, "big")
        _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        _p(f"\theader index \t|  {self.mah.hdr_idx}")
        if b"00003" != self.mah.cc_area[:5]:
            return {}
        _p(f"\tSPT period   \t|  {self.mah_context.spt}")

    def _parse_data_mm(self, mm, i):
        # DOX loggers they don't use mask
        _p(f"\n\tmeasurement #   |  {self.mm_i}")
        t_spt = int(self.mah_context.spt)
        t = self.mah.timestamp_epoch + (self.mm_i * t_spt)
        is_do2 = self.mah.file_type.decode() == 'DO2'
        n = 8 if is_do2 else 6

        # build dictionary measurements
        self.d_mm[t] = mm[i:i + n]

        # keep track of how many we decoded
        self.mm_i += 1

        # return current index of measurements' array
        return i + n

    def _create_csv_file(self):

        # file columns differ
        is_do2 = self.mah.file_type.decode() == 'DO2'

        # CSV file header
        csv_path = (self.file_path[:-4] + '_DissolvedOxygen.csv')
        f_csv = open(csv_path, 'w')
        if is_do2:
            cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),'\
                   'Dissolved Oxygen (mg/l),Dissolved Oxygen (%),'\
                   'DO Temperature (C),Water Detect (%)\n'
        else:
            cols = 'ISO 8601 Time,elapsed time (s),agg. time(s),' \
                   'Dissolved Oxygen (mg/l),Dissolved Oxygen (%),' \
                   'DO Temperature (C)\n'
        f_csv.write(cols)

        # ct: cumulative time
        ct = 0
        for t, m in self.d_mm.items():
            # m : b'\x80\x03\x80(\x07\x04\x00\x11'
            # m = dos -0.04 dop -0.40 dot 17.97
            dos = do16_to_float(int.from_bytes(m[0:2], "big"))
            dop = do16_to_float(int.from_bytes(m[2:4], "big"))
            dot = do16_to_float(int.from_bytes(m[4:6], "big"))
            if is_do2:
                # wat is directly in mV
                wat = int.from_bytes(m[6:8], "big")
                wat = int((wat / 3000) * 100)

            # calculate times
            et = int(self.mah_context.spt)
            ct += et
            str_t = datetime.utcfromtimestamp(t).isoformat() + ".000"

            # only two decimals
            dos = '{:.2f}'.format(dos)
            dop = '{:.2f}'.format(dop)
            dot = '{:.2f}'.format(dot)
            if is_do2:
                wat = '{:.2f}'.format(wat)
                s = f'{str_t},{et},{ct},{dos},{dop},{dot},{wat}\n'
            else:
                s = f'{str_t},{et},{ct},{dos},{dop},{dot}\n'
            f_csv.write(s)

        # close the file
        f_csv.close()
