# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


def header_factory(file_path):
    with open(file_path, 'rb') as fid:
        header_string = fid.read(500).decode('IBM437')
    return Header(header_string)


def cut_out(string, start_cut, end_cut):
    return string[:start_cut] + string[end_cut:]


DEPLOYMENT_NUMBER = 'DPL'
IS_ACCELEROMETER = 'ACL'
IS_LED = 'LED'
IS_MAGNETOMETER = 'MGN'
IS_PHOTO_DIODE = 'PHD'
IS_PRESSURE = 'PRS'
IS_TEMPERATURE = 'TMP'
ORIENTATION_BURST_COUNT = 'BMN'
ORIENTATION_BURST_RATE = 'BMR'
ORIENTATION_INTERVAL = 'ORI'
PRESSURE_BURST_COUNT = 'PRN'
PRESSURE_BURST_RATE = 'PRR'
START_TIME = 'CLK'
STATUS = 'STS'
TEMPERATURE_INTERVAL = 'TRI'


class Header:
    type_int = [
        DEPLOYMENT_NUMBER,
        ORIENTATION_BURST_COUNT,
        ORIENTATION_BURST_RATE,
        ORIENTATION_INTERVAL,
        PRESSURE_BURST_COUNT,
        PRESSURE_BURST_RATE,
        STATUS,
        TEMPERATURE_INTERVAL,
    ]
    type_bool = [
        IS_ACCELEROMETER,
        IS_LED,
        IS_MAGNETOMETER,
        IS_PHOTO_DIODE,
        IS_PRESSURE,
        IS_TEMPERATURE,
    ]

    def __init__(self, header_string):
        self.header_string = header_string
        self._header = {}

    def tag(self, tag):
        return self._header.get(tag)

    def parse_header(self):
        header_string = self._crop_header_block(self.header_string)
        header_string = self._remove_logger_info(header_string)
        header_string = self._remove_header_tags(header_string)
        self._header = self._parse_tags(header_string)

    def _crop_header_block(self, header_block):
        self._validate_header_block(header_block)
        mhe_index = header_block.find('HDE')
        return header_block[:mhe_index+5]

    def _remove_logger_info(self, header_string):
        lis = header_string.find('LIS')
        lie = header_string.find('LIE')
        return cut_out(header_string, lis, lie+5)

    def _remove_header_tags(self, header_string):
        for tag_to_remove in ['HDS', 'HDE', 'MHS', 'MHE']:
            index = header_string.find(tag_to_remove)
            header_string = cut_out(header_string, index, index+5)
        return header_string

    def _parse_tags(self, header_string):
        header_lines = header_string.split('\r\n')[:-1]
        header = {}
        for tag_and_value in header_lines:
            tag, value = tag_and_value.split(' ', 1)
            header[tag] = self._convert_to_type(tag, value)
        return header

    def _validate_header_block(self, header_string):
        if not header_string.startswith('HDS'):
            raise ValueError('Header must start with HDS')
        mandatory_tags = ['HDE', 'MHS', 'MHE', 'LIS', 'LIE']
        for tag in mandatory_tags:
            if tag not in header_string:
                raise ValueError(tag + ' tag missing in header')

    def _convert_to_type(self, tag, value):
        if tag in self.type_bool:
            return value == '1'
        if tag in self.type_int:
            return int(value)
        return value

    @property
    def orientation_burst_rate(self):
        return self._header['BMR']

    @property
    def orientation_burst_count(self):
        return self._header['BMN']

    @property
    def orientation_interval(self):
        return self._header['ORI']

    @property
    def temperature_interval(self):
        return self._header['TRI']

    @property
    def pressure_burst_rate(self):
        return self._header['PRR'] if 'PRR' in self._header.keys() else None

    @property
    def pressure_burst_count(self):
        return self._header['PRN'] if 'PRN' in self._header.keys() else None

    @property
    def is_temperature(self):
        return self._header['TMP']

    @property
    def is_accelerometer(self):
        return self._header['ACL']

    @property
    def is_magnetometer(self):
        return self._header['MGN']

    @property
    def is_led(self):
        return self._header['LED']

    @property
    def is_pressure(self):
        return self._header['PRS'] if 'PRS' in self._header.keys() else False

    @property
    def is_photo_diode(self):
        return self._header['PHD'] if 'PHD' in self._header.keys() else False

    @property
    def start_time(self):
        return self._header['CLK']

    @property
    def is_orient(self):
        return self.is_accelerometer or self.is_magnetometer
