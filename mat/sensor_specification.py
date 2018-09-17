"""
This module specifies the unique qualities of each sensor.
"""

from collections import namedtuple
from mat import converter


SensorSpec = namedtuple('SensorSpec', [
    'name',
    'enabled_tag',
    'order',
    'channels',
    'interval_tag',
    'burst_rate_tag',
    'burst_count_tag',
    'data_type',
    'channel_name',
    'channel_units',
    'converter']
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
               channel_name='Temperature',
               channel_units='C',
               converter=converter.Temperature),

    SensorSpec(name='Pressure',
               enabled_tag='PRS',
               order=2,
               channels=1,
               interval_tag='ORI',
               burst_rate_tag='PRR',
               burst_count_tag='PRN',
               data_type='uint16',
               channel_name='Pressure',
               channel_units='psi',
               converter=converter.Pressure),

    SensorSpec(name='Light',
               enabled_tag='PHD',
               order=3,
               channels=1,
               interval_tag='TRI',
               burst_rate_tag=None,
               burst_count_tag=None,
               data_type='uint16',
               channel_name='Light',
               channel_units='%',
               converter=converter.Light.factory),

    SensorSpec(name='Accelerometer',
               enabled_tag='ACL',
               order=4,
               channels=3,
               interval_tag='ORI',
               burst_rate_tag='BMR',
               burst_count_tag='BMN',
               data_type='int16',
               channel_name=['Ax', 'Ay', 'Az'],
               channel_units='g',
               converter=converter.Accelerometer.factory),

    SensorSpec(name='Magnetometer',
               enabled_tag='MGN',
               order=5,
               channels=3,
               interval_tag='ORI',
               burst_rate_tag='BMR',
               burst_count_tag='BMN',
               data_type='int16',
               channel_name=['Mx', 'My', 'Mz'],
               channel_units='mG',
               converter=converter.Magnetometer.factory)
]
