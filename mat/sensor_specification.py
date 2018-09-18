"""
This module specifies the unique qualities of each sensor.
"""

from collections import namedtuple
from mat.accelerometer_factory import accelerometer_factory
from mat.magnetometer_factory import magnetometer_factory
from mat.light import Light
from mat.pressure import Pressure
from mat.temperature import Temperature


SensorSpec = namedtuple('SensorSpec', [
    'name',
    'enabled_tag',
    'order',
    'channels',
    'interval_tag',
    'burst_rate_tag',
    'burst_count_tag',
    'data_type',
    'header',
    'converter',
    'format']
)

AVAILABLE_SENSORS = [
    SensorSpec(name='Temperature',
               enabled_tag='TMP',
               order=1,
               channels=1,
               interval_tag='TRI',
               burst_rate_tag=None,
               burst_count_tag=None,
               data_type='uint16',
               header='Temperature (C)',
               converter=Temperature,
               format='{:0.4f}'),

    SensorSpec(name='Pressure',
               enabled_tag='PRS',
               order=2,
               channels=1,
               interval_tag='ORI',
               burst_rate_tag='PRR',
               burst_count_tag='PRN',
               data_type='uint16',
               header='Pressure (psi)',
               converter=Pressure,
               format='{:0.2f}'),

    SensorSpec(name='Light',
               enabled_tag='PHD',
               order=3,
               channels=1,
               interval_tag='TRI',
               burst_rate_tag=None,
               burst_count_tag=None,
               data_type='uint16',
               header='Light (%)',
               converter=Light,
               format='{:0.1f}'),

    SensorSpec(name='Accelerometer',
               enabled_tag='ACL',
               order=4,
               channels=3,
               interval_tag='ORI',
               burst_rate_tag='BMR',
               burst_count_tag='BMN',
               data_type='int16',
               header='Ax (g), Ay (g), Az (g)',
               converter=accelerometer_factory,
               format='{:0.4f},{:0.4f},{:0.4f}'),

    SensorSpec(name='Magnetometer',
               enabled_tag='MGN',
               order=5,
               channels=3,
               interval_tag='ORI',
               burst_rate_tag='BMR',
               burst_count_tag='BMN',
               data_type='int16',
               header='Mx (mG), My (mG), Mz (mG)',
               converter=magnetometer_factory,
               format='{:0.2f},{:0.2f},{:0.2f}')
]
