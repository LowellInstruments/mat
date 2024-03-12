from numpy import array


DEFAULT_PRA = 3
DEFAULT_PRB = 0.0016
DEFAULT_PRC = 0
DEFAULT_PRD = 0


class Pressure:
    def __init__(self, calibration,
                 prc=DEFAULT_PRC, prd=DEFAULT_PRD):
        coefficients = calibration.coefficients
        pra = coefficients.get('PRA', DEFAULT_PRA)
        prb = coefficients.get('PRB', DEFAULT_PRB)
        self.pressure_slope = array([prb], dtype='float')
        self.pressure_offset = array([pra], dtype='float')

    def convert(self, raw_pressure):
        # raw_pressure: single value such as 64723
        # slope: [0.00163531]
        # offset: [2.84902716]
        # v: [74.94014981]
        v = ((self.pressure_slope * raw_pressure + self.pressure_offset)
             * 0.689475728)
        return v
