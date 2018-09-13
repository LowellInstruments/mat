# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

"""
Convert raw odl data to si values
calibration is a calibration object
"""

from mat.accelerometer_factory import accelerometer_factory
from mat.magnetometer_factory import magnetometer_factory
from mat.light import Light
from mat.pressure import Pressure
from mat.temperature import Temperature


class Converter:
    def __init__(self, calibration):
        self.temperature_converter = Temperature(calibration)
        self.accelerometer_converter = accelerometer_factory(calibration)
        self.magnetometer_converter = magnetometer_factory(calibration)
        self.pressure_converter = Pressure(calibration)
        self.light_converter = Light(calibration)

    def temperature(self, raw_temperature):
        return self.temperature_converter.convert(raw_temperature)

    def accelerometer(self, raw_accelerometer, temperature=None):
        if self.accelerometer_converter is None:
            return None
        return self.accelerometer_converter.convert(raw_accelerometer,
                                                    temperature)

    def magnetometer(self, raw_magnetometer, temperature=None):
        if self.magnetometer_converter is None:
            return None
        return self.magnetometer_converter.convert(raw_magnetometer,
                                                   temperature)

    def pressure(self, raw_pressure):
        return self.pressure_converter.convert(raw_pressure)

    def light(self, raw_light):
        return self.light_converter.convert(raw_light)
