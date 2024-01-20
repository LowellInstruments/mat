from math import ceil

# chunk size
CS = 256
# micro-header size
UHS = 8


class ParserLixFile:
    def __init__(self):
        self.path = None
        self.bb = bytes()
        # sm: sensor mask
        self.sm = None
        # lm: length of measurement
        self.lm = 0
        # nm: number of measurement
        self.nm = 0
        # i: index to iterate bytes
        self.i = 0
        # ny: number of carry bytes
        self.ny = 0

    def parse_lix_file(self, p):
        self.path = p
        with open(self.path, 'rb') as f:
            self.bb = f.read()
        self._parse_macro_header()
        assert self.sm
        self._parse_all_chunks()

    def _parse_all_chunks(self):
        for i in range(ceil(len(self.bb) / CS)):
            self._parse_carry()
            self._parse_one_chunk()

    def _parse_carry(self):
        yb = self.bb[self.i + UHS: self.i + UHS + self.ny]
        # use current sensor mask to parse carry bytes
        print(yb)

    def _parse_one_chunk(self):
        # todo ---> parse micro_header
        ub = self.bb[self.i: self.i + UHS]

        # db: data bytes, parse according sensor mask
        # todo --> parse data bytes
        db = self.bb[self.i + UHS + self.ny: self.i + CS]

        # increase the global number of measurements
        self.nm += 1
        # todo --> set number of carry bytes
        self.ny = 0

    def _parse_macro_header(self):
        ab = self.bb[:CS]
        # get length of first measurement from macro-header
        self.lm = 6969
        # update index
        self.i += CS

    def _calc_measurement_length(self):
        # todo: do this based on sensor mask lm
        return 10

