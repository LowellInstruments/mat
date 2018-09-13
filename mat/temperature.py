from numpy import log


class Temperature:
    def __init__(self, calibration):
        coefficients = calibration.coefficients
        self.is_active = {'TMA', 'TMB', 'TMC', 'TMR'} <= set(coefficients)
        if self.is_active:
            self.tma = coefficients['TMA']
            self.tmb = coefficients['TMB']
            self.tmc = coefficients['TMC']
            self.tmr = coefficients['TMR']

    def convert(self, raw_temperature):
        if self.is_active:
            temp = (raw_temperature * self.tmr) / (65535 - raw_temperature)
            return 1 / (self.tma +
                        self.tmb * log(temp) +
                        self.tmc * (log(temp)) ** 3) - 273.15
        return None
