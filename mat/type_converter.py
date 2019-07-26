import numpy as np


def type_factory(type):
    type_map = {'bcd2p2': BCD2p2}
    if type in ['int16', 'uint16']:
        return NumpyType(type)
    else:
        return type_map[type](type)


class DataType:
    def __init__(self, data_type):
        self.data_type = data_type

    def convert(self, raw_values):
        pass


class NumpyType(DataType):
    def convert(self, raw_value):
        return raw_value.astype(self.data_type)


class BCD2p2(DataType):
    """ Binary Coded Decimal 2 digits, point, 2 digits """
    def __init__(self, data_type):
        super().__init__(data_type)
        self._convert_fcn = np.vectorize(self._dec_to_bcd)

    def convert(self, raw_values):
        return self._convert_fcn(raw_values)

    def _dec_to_bcd(self, value):
        output = 0
        for i in range(4):
            shift = 12 - 4*i
            multiplier = 10 / (10**i)
            output += (value >> shift & 15) * multiplier
        return output
