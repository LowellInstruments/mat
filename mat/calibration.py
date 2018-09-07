# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

"""
Read/write calibration data from a logger or file

Calibration data is found in .lid and .lis files immediately proceeding
the header. The calibration data is found within the HSS and HSE tags. Each
calibration value is on a separate line.

There have been three different versions of calibration coefficients since
the introduction of the MAT logger. This module is responsible for managing
how the various versions are read and written.

V1 Calibration isn't found "in the wild" so it will be ignored

V2 Calibration is stored in the data file in the following way:
3 letter tag, 1 hex number for length, ascii numeric value
eg. AXX61.1201 -- AXX is the tag, 6 is the data length, 1.1201 is the value

V3 Calibration is stored in the data file in the following way:
3 letter tag, 5 byte ascii-85 encoded single precision float
eg. AXX^3r#p -- AXX is the tag, and "^3r#p" is -0.247291 encoded in ascii85
The format is
"""

from abc import ABC, abstractclassmethod, abstractmethod
from mat import ascii85


class Calibration(ABC):
    def __init__(self, coefficients):
        """
        coefficients is passed to the subclasses with values as strings
        The subclasses must convert the string values to numeric values and
        pass them back to this __init__ method
        The V2 __init__ needs to convert plain text ascii to float
        The V3 __init__ needs to convert five ascii85 characters to float
        """
        if not coefficients:
            coefficients = self.load_generic()
            self.is_generic = True
        else:
            self.is_generic = False

        for tag in coefficients:
            coefficients[tag] = float(coefficients[tag])
        self.coefficients = coefficients

    @abstractclassmethod
    def load_from_string(self, calibration_string):
        pass  # pragma: no cover

    @abstractmethod
    def make_serial_string(self):
        pass  # pragma: no cover

    def load_generic(self):
        coefficients = {'AXX': 1, 'AXY': 0, 'AXZ': 0, 'AXC': 0, 'AXV': 0,
                        'AYX': 0, 'AYY': 1, 'AYZ': 0, 'AYC': 0, 'AYV': 0,
                        'AZX': 0, 'AZY': 0, 'AZZ': 1, 'AZC': 0, 'AZV': 0,
                        'RVN': 2,
                        'TMO': 0,
                        'TMR': 10000,
                        'TMA': 0.0011238100354,
                        'TMB': 0.0002349457073,
                        'TMC': 0.0000000848361,
                        'MXX': 1, 'MXY': 0, 'MXZ': 0, 'MXV': 0,
                        'MYX': 0, 'MYY': 1, 'MYZ': 0, 'MYV': 0,
                        'MZX': 0, 'MZY': 0, 'MZZ': 1, 'MZV': 0,
                        'PRA': 3,
                        'PRB': 0.0016,
                        'PHA': 0,
                        'PHB': 0}
        return coefficients
