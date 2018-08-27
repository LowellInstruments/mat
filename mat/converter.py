"""
Convert raw odl data to si values
hoststorage is a hoststorage object
"""

import numpy as np
from abc import ABC, abstractmethod


class Accelerometer(ABC):
    @staticmethod
    def accelerometer_factory(hoststorage):
        hs_dict = hoststorage.hs_dict
        if {'AXX', 'AXY', 'AXZ', 'AYX', 'AYY', 'AYZ', 'AZX', 'AZY', 'AZZ'} <= set(hs_dict):
            return NewAccelerometer(hs_dict)
        elif {'AXA', 'AXB', 'AYA', 'AYB', 'AZA', 'AZB'} <= set(hs_dict):
            return OldAccelerometer(hs_dict)
        else:
            return None

    @abstractmethod
    def __init__(self, hs):
        pass

    @abstractmethod
    def convert(self, raw_accelerometer, temperature=None):
        pass


class OldAccelerometer(Accelerometer):
    def __init__(self, hs):
        self.slope = np.array([[1 / hs['AXB']], [1 / hs['AYB']], [1 / hs['AZB']]])
        self.offset = np.array([[hs['AXA']], [hs['AYA']], [hs['AZA']]])

    def convert(self, raw_accelerometer, temperature=None):
        return -raw_accelerometer * self.slope - self.offset


class NewAccelerometer(Accelerometer):
    def __init__(self, hs):
        self.gain = np.array([[hs['AXX'], hs['AXY'], hs['AXZ']],
                              [hs['AYX'], hs['AYY'], hs['AYZ']],
                              [hs['AZX'], hs['AZY'], hs['AZZ']]])
        self.offset = np.array([[hs['AXV']], [hs['AYV']], [hs['AZV']]])
        self.cubic = np.array([[hs['AXC']], [hs['AYC']], [hs['AZC']]])

    def convert(self, raw_accelerometer, temperature=None):
        raw_accelerometer = raw_accelerometer / 1024.
        return np.dot(self.gain, raw_accelerometer) + self.offset + self.cubic * raw_accelerometer ** 3


class Magnetometer(ABC):
    @staticmethod
    def magnetometer_factory(hoststorage):
        hs_dict = hoststorage.hs_dict
        if {'MXX', 'MXY', 'MXZ', 'MYX', 'MYY', 'MYZ', 'MZX', 'MZY', 'MZZ', 'AXV', 'AYV', 'AZV',
            'AXC', 'AYC', 'AZC', 'TMX', 'TMY', 'TMZ', 'MRF'} <= set(hs_dict):
            return TempCompensatedMagnetometer(hs_dict)
        elif {'MXX', 'MXY', 'MXZ', 'MYX', 'MYY', 'MYZ', 'MZX', 'MZY', 'MZZ', 'AXV', 'AYV', 'AZV',
              'AXC', 'AYC', 'AZC'} <= set(hs_dict):
            return NewMagnetometer(hs_dict)
        elif {'MXA', 'MXS', 'MYA', 'MYS', 'MZA', 'MZS'} <= set(hs_dict):
            return OldMagnetometer(hs_dict)
        else:
            return None

    @abstractmethod
    def __init__(self, hs):
        pass

    @abstractmethod
    def convert(self, raw_magnetometer, temperature=None):
        pass


class OldMagnetometer(Magnetometer):
    def __init__(self, hs):
        self.slope = np.array([[hs['MXS']], [hs['MYS']], [hs['MZS']]])
        self.offset = np.array([[hs['MXA']], [hs['MYA']], [hs['MZA']]])

    def convert(self, raw_magnetometer, temperature=None):
        return (raw_magnetometer + self.offset) * self.slope


class NewMagnetometer(Magnetometer):
    def __init__(self, hs):
        self.hard_iron = np.array([[hs['MXV']], [hs['MYV']], [hs['MZV']]])
        self.soft_iron = np.array([[hs['MXX'], hs['MXY'], hs['MXZ']],
                                   [hs['MYX'], hs['MYY'], hs['MYZ']],
                                   [hs['MZX'], hs['MZY'], hs['MZZ']]])

    def convert(self, raw_magnetometer, temperature=None):
        return np.dot(self.soft_iron, raw_magnetometer + self.hard_iron)


class TempCompensatedMagnetometer(NewMagnetometer):
    def __init__(self, hs):
        super().__init__(hs)
        self.temperature_slope = np.array([[hs['TMX'], hs['TMY'], hs['TMZ']]]).T
        self.temp_reference = np.array([hs['MRF']])

    def convert(self, raw_magnetometer, temperature=None):
        """
        NOTE: temperature must be a numpy array, even if it is a single value
        """
        magnetometer = super().convert(raw_magnetometer)
        if temperature is None:
            return magnetometer
        temp_range = [-20, 50]
        temperature[temperature < temp_range[0]] = temp_range[0]
        temperature[temperature > temp_range[1]] = temp_range[1]
        assert temperature.shape == (raw_magnetometer.shape[1],)
        temperature_delta = np.tile(temperature, (3, 1)) - self.temp_reference
        magnetometer = magnetometer + temperature_delta * self.temperature_slope
        return magnetometer


class Pressure:
    @staticmethod
    def pressure_factory(hoststorage):
        """ Pressure currently only has one implementation. This is for future expansion. """
        hs_dict = hoststorage.hs_dict
        if {'PRA', 'PRB'} <= set(hs_dict):
            return Pressure(hs_dict)
        else:
            return Pressure({'PRA': 3, 'PRB': 0.0016})

    def __init__(self, hs):
        self.pressure_slope = np.array([hs['PRB']], dtype='float')
        self.pressure_offset = np.array([hs['PRA']], dtype='float')

    def convert(self, raw_pressure):
        return self.pressure_slope * raw_pressure + self.pressure_offset


class Temperature:
    @staticmethod
    def temperature_factory(hoststorage):
        hs_dict = hoststorage.hs_dict
        if {'TMA', 'TMB', 'TMC', 'TMR'} <= set(hs_dict):
            return Temperature(hs_dict)
        else:
            return None

    def __init__(self, hs):
        self.tma = hs['TMA']
        self.tmb = hs['TMB']
        self.tmc = hs['TMC']
        self.tmr = hs['TMR']

    def convert(self, raw_temperature):
        temperature = (raw_temperature * self.tmr) / (65535 - raw_temperature)
        temperature = 1 / (self.tma + self.tmb * np.log(temperature) + self.tmc * (np.log(temperature)) ** 3) - 273.15
        return temperature


class Light:
    @staticmethod
    def light_factory(hoststorage):
        hs_dict = hoststorage.hs_dict
        if {'PDA', 'PDB'} <= set(hs_dict):
            return Light(hs_dict)
        else:
            return Light({'PDA': 100., 'PDB': -100/4096})

    def __init__(self, hs):
        self.pda = hs['PDA']
        self.pdb = hs['PDB']

    def convert(self, raw_light):
        is_bad_val = raw_light > 4096
        light_val = raw_light * self.pdb + self.pda
        light_val[is_bad_val] = -1
        return light_val


class Converter:
    def __init__(self, hoststorage):
        self.temperature_converter = Temperature.temperature_factory(hoststorage)
        self.accelerometer_converter = Accelerometer.accelerometer_factory(hoststorage)
        self.magnetometer_converter = Magnetometer.magnetometer_factory(hoststorage)
        self.pressure_converter = Pressure.pressure_factory(hoststorage)
        self.light_converter = Light.light_factory(hoststorage)

    def temperature(self, raw_temperature):
        if self.temperature_converter is None:
            return None
        return self.temperature_converter.convert(raw_temperature)

    def accelerometer(self, raw_accelerometer, temperature=None):
        if self.accelerometer_converter is None:
            return None
        return self.accelerometer_converter.convert(raw_accelerometer, temperature)

    def magnetometer(self, raw_magnetometer, temperature=None):
        if self.magnetometer_converter is None:
            return None
        return self.magnetometer_converter.convert(raw_magnetometer, temperature)

    def pressure(self, raw_pressure):
        if self.pressure_converter is None:
            return None
        return self.pressure_converter.convert(raw_pressure)

    def light(self, raw_light):
        if self.light_converter is None:
            return None
        return self.light_converter.convert(raw_light)

