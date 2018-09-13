# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

from mat.utils import cut_out, parse_tags


def header_factory(file_path):
    with open(file_path, 'rb') as fid:
        header_string = fid.read(500).decode('IBM437')
    return Header(header_string)


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
        header_dict = parse_tags(header_string)
        self._header = self._convert_to_type(header_dict)

    def _crop_header_block(self, header_block):
        self._validate_header_block(header_block)
        mhe_index = header_block.find('HDE')
        return header_block[:mhe_index+5]

    def _remove_logger_info(self, header_string):
        lis = header_string.find('LIS')
        lie = header_string.find('LIE')
        if lis > -1 and lie > -1:
            return cut_out(header_string, lis, lie+5)
        else:
            return header_string

    def _remove_header_tags(self, header_string):
        for tag_to_remove in ['HDS', 'HDE', 'MHS', 'MHE']:
            index = header_string.find(tag_to_remove)
            header_string = cut_out(header_string, index, index+5)
        return header_string

    def _validate_header_block(self, header_string):
        if not header_string.startswith('HDS'):
            raise ValueError('Header must start with HDS')
        mandatory_tags = ['HDE', 'MHS', 'MHE']
        for tag in mandatory_tags:
            if tag not in header_string:
                raise ValueError(tag + ' tag missing in header')

    def _convert_to_type(self, dictionary):
        for tag, value in dictionary.items():
            if tag in self.type_bool:
                dictionary[tag] = value == '1'
            if tag in self.type_int:
                dictionary[tag] = int(value)
        return dictionary
