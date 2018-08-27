"""
Parse and make human readable the information from a .lid/.lis file header
"""


class Header:
    type_int = ['BMN', 'BMR', 'DPL', 'STS', 'ORI', 'TRI', 'PRR', 'PRN']
    type_bool = ['ACL', 'LED', 'MGN', 'TMP', 'PRS', 'PHD']

    def __init__(self, file_obj):
        file_pos = file_obj.tell()
        assert file_obj.mode == 'rb', 'File must be open for binary reading'
        self._raw_header_string = self.read_header(file_obj)
        self._header = self.parse_tags(self._raw_header_string)
        file_obj.seek(file_pos)

    def read_header(self, file_obj):
        file_obj.seek(0, 0)
        first_500 = file_obj.read(500).decode('IBM437')
        assert first_500.startswith('HDS'), 'Header must start with HDS'
        mhe_index = first_500.find('MHE')
        return first_500[:mhe_index+3]

    def parse_tags(self, raw_string):
        # get rid of the logger info section (LIE to LIS tags)
        lis_index = raw_string.find('LIS')
        lie_index = raw_string.find('LIE')
        if lis_index > -1 and lie_index > -1:
            raw_string = raw_string[:lis_index] + raw_string[lie_index + 5:]

        # get rid of the HDS and HDE tags
        raw_string = raw_string[5:-5]
        header_tag_value_list = raw_string.split('\r\n')

        header = {}
        for tag_value in header_tag_value_list:
            if tag_value.startswith('MHS') or tag_value.startswith('MHE'):
                continue
            tag, value = tag_value.split(' ', 1)
            if tag in self.type_bool:
                header[tag] = True if value == '1' else False
            elif tag in self.type_int:
                header[tag] = int(value)
            else:
                header[tag] = value

        return header

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
