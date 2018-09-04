# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


def header_factory(file_path):
    with open(file_path, 'rb') as fid:
        header_string = fid.read(500).decode('IBM437')
    return Header(header_string)


def cut_out(string, start_cut, end_cut):
    return string[:start_cut] + string[end_cut:]


class Header:
    type_int = ['BMN', 'BMR', 'DPL', 'STS', 'ORI', 'TRI', 'PRR', 'PRN']
    type_bool = ['ACL', 'LED', 'MGN', 'TMP', 'PRS', 'PHD']

    def __init__(self, header_string):
        self.header_string = header_string

    def parse_header(self):
        header_string = self._crop_header_block(self.header_string)
        header_string = self._remove_logger_info(header_string)
        header_string = self._remove_header_tags(header_string)
        header = self._parse_tags(header_string)
        return header

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
            converted_value = True if value == '1' else False
        elif tag in self.type_int:
            converted_value = int(value)
        else:
            converted_value = value
        return converted_value
