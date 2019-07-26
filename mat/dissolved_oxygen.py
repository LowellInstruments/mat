import numpy as np
from mat.meter import Meter


"""
Dissolved oxygen are read from the sensor in engineering units (no calibration
or conversion required). The values are written to the .lid file as 2 byte 
unsigned ints in a modified BCD format (xx.xx) where there is a decimal 
between the first and last two digits.  
e.g. an int value of 9847 is 0x2677 which yields a final value of 26.77
"""


class DissolvedOxygen(Meter):
    def __init__(self, hs=None):
        self._convert_fcn = np.vectorize(self._dec_to_bcd)

    def convert(self, encoded_bcd):
        return self._convert_fcn(encoded_bcd)

    def _dec_to_bcd(self, value):
        output = 0
        for i in range(4):
            shift = 12 - 4*i
            multiplier = 10 / (10**i)
            output += (value >> shift & 15) * multiplier
        return output
