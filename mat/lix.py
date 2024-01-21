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
        # i: index bytes
        self.i = 0
        # named tuple macro-header
        self.mah = namedtuple("MacroHeader",
                              "logger_type "
                              "sm")
        # dictionary measurements
        self.d_measurements = None
        # dictionary micro-headers
        self.d_mih = None

    def _parse_macro_header(self):
        mah = self.bb[:CS]
        # update index
        self.i += CS

    def parse_lix_file(self, p):
        self.path = p
        with open(self.path, 'rb') as f:
            self.bb = f.read()
        self._parse_macro_header()
        assert self.sm
        self._parse_data()

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

        print(len(measurements), measurements)
        print(len(micro_headers), micro_headers)

        # build dictionary measurements
        self.d_measurements = dict()
        while 1:
            # measurements are of variable length
            break

        # build dictionary micro_headers
        self.d_mih = dict()
        for i in range(0, UHS, len(micro_headers)):
            pass


if __name__ == '__main__':
    p = ParserLixFile()
    p._parse_data()
