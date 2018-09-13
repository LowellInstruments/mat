from numpy import log


class Temperature:
    def __init__(self, calibration):
        coefficients = calibration.coefficients
        self.tma = coefficients['TMA']
        self.tmb = coefficients['TMB']
        self.tmc = coefficients['TMC']
        self.tmr = coefficients['TMR']

    def convert(self, raw_temperature):
        temp = (raw_temperature * self.tmr) / (65535 - raw_temperature)
        return 1 / (self.tma +
                    self.tmb * log(temp) +
                    self.tmc * (log(temp)) ** 3) - 273.15
