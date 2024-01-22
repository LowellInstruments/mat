from collections import namedtuple
from math import ceil

# chunk size
CS = 256
# micro-header size
UHS = 8
# flag debug
debug = 1


class ParserLixFile:
    def __init__(self):
        self.path = None
        # all file bytes
        self.bb = bytes()
        # sm: sensor mask
        self.sm = None
        # named tuple macro-header
        self.mah = namedtuple("MacroHeader",
                              "logger_type "
                              "sm")
        # dictionary measurements
        self.d_measurements = dict()
        # dictionary micro-headers
        self.d_mih = dict()

    def _parse_macro_header(self):
        mah = self.bb[:CS]

    def parse_lix_file(self, p):
        self.path = p
        with open(self.path, 'rb') as f:
            self.bb = f.read()
        self._parse_macro_header()
        assert self.sm
        self._parse_data()

    def _parse_data_mih(self, mi, i):
        # 2B battery, 1B header index % 255,
        # 1B ECL, 4B epoch
        bat = mi[:i+2]
        idx = mi[i+2]
        ecl = mi[i+3]
        t = mi[i+4:i+8]
        self.d_mih[t] = 'bat, idx, ECL'

    def _parse_data_measurement(self, mm, i):
        mk = (mm[i] & 0xc0) >> 6
        if mk == 0:
            # no sensor mask, time simple
            t = mm[i] & 0x3F
            i += 1
        elif mk == 1:
            # no sensor mask, time extended
            t = (mm[i] & 0x3F) << 8
            t += mm[i+1]
            i += 2
        elif mk == 2:
            # yes sensor mask, time simple
            self.sm = mm[i] & 0x3F
            t = mm[i+1]
            i += 2
        else:
            # yes sensor mask, time extended
            self.sm = mm[i] & 0x3F
            t = (mm[i] & 0x3F) << 8
            t += mm[i+1]
            i += 3

        # get measurement length from sensor mask
        n = 6
        self.d_measurements[t] = 'sensor1, sensor2, sensor3'
        i += n
        return i

    def _parse_data(self):
        if debug:
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
        n = ceil(len(data) / CS)
        for i in range(0, CS * n, CS):
            measurements += data[i+UHS:i+CS]
            micro_headers += data[i:i+UHS]

        # build dictionary measurements
        i = 0
        while 1:
            try:
                # measurements have variable length
                i += self._parse_data_measurement(measurements, i)
            except IndexError:
                break

        # build dictionary micro_headers
        for i in range(0, UHS, len(micro_headers)):
            self._parse_data_mih(micro_headers, i)

        # maybe fusion both dictionaries here


if __name__ == '__main__':
    plf = ParserLixFile()
    plf._parse_data()
