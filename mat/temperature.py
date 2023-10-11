from numpy import log


ZERO_KELVIN = -273.15
MAX_INT16 = 65535


class Temperature:
    def __init__(self, calibration):
        coefficients = calibration.coefficients
        self.tma = coefficients['TMA']
        self.tmb = coefficients['TMB']
        self.tmc = coefficients['TMC']
        self.tmd = 0
        if 'TMD' in coefficients.keys():
            self.tmd = coefficients['TMD']
        self.tmr = coefficients['TMR']

    def convert(self, raw_temperature):
        try:
            temp = (raw_temperature * self.tmr) / (MAX_INT16 - raw_temperature)
            return 1 / (self.tma +
                        self.tmb * log(temp) + self.tmd*(log(temp))**2 +
                        self.tmc * (log(temp)) ** 3) + ZERO_KELVIN
        except ZeroDivisionError:
            return ZERO_KELVIN
