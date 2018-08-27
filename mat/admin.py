from mat.matcomm import Logger


class LoggerAdmin(Logger):
    def __init__(self):
        Logger.__init__(self)

    def set_mag_range(self, value):
        self.command('MGR', value)

    def set_accel_range(self, value):
        self.command('ACR', value)

    def erase_LI(self):
        self.command('ULI')  # Unlock info memory
        self.command('ELI')  # Erase info memory

    def write_LI(self, li_dict):
        '''
        :type li_dict: dict
        '''
        self.command('ULI')  # Unlock info memory
        self.command('ELI')  # Erase info memory
        address = 0
        for tag, value in li_dict.items():
            if tag == 'CA':
                value = round(float(value)*256)
                if value < 0:
                    # if it's less than zeros subtract (add negative) from 65536
                    value = 65536 + value
                value = '%04x' % value
                value = value[2:4] + value[0:2]

            if tag == 'PC' or tag == 'DP':
                value = value.zfill(4)  # Pad with zeros

            if tag == 'SN':
                if len(value) == 8:
                    raise RuntimeError('Serial number cannot be 8 characters long')

            hex_address = '%04x' % address
            hex_address = hex_address[2:4] + hex_address[0:2]
            length = len(value)
            length_binary = chr(length)
            address += length + len(tag) + len(length_binary)

            write_string = hex_address + tag + length_binary + value
            self.command('WLI', write_string)
            self.command('ULI')

        hex_address = '%04x' % address
        hex_address = hex_address[2:4] + hex_address[0:2]
        write_string = hex_address + '##'
        self.command('WLI', write_string)
        self.load_logger_info()

    def clear_page_count(self):
        self.command('CPC')

    def sleep(self):
        self.command('sleep')

    def mag_self_test(self):
        mst_string = self.command('MST')
        channels = ['x', 'y', 'z']
        result = {}
        for i in range(3):
            hex_val = mst_string[2:4] + mst_string[0:2]
            int_val = int(hex_val, 16)
            mst_string = mst_string[4:]
            if 243 <= int_val <= 575:
                result[channels[i]] = {'Passed': True, 'Value': int_val}
            else:
                result[channels[i]] = {'Passed': False, 'Value': int_val}
        return result

    def sd_speed_test(self):
        return self.command('SPD')

    def start_bsl(self):
        self.command('BSL')

    def calibrate_crystal(self):
        self.command('CAL')

    def erase_host_storage(self):
        self.command('EHS')  # erase host storage

    def write_host_storage(self, hs_file):
        self.erase_host_storage()
        self.command('WHS', '0000HSS')  # write the opening HSS tag

        address = 3
        for formatted_tag_val in hs_file.format_for_write():  # format_for_write is a generator
            hex_address = '%04X' % address
            hex_address = hex_address[2:4] + hex_address[0:2]
            self.command('WHS', hex_address + formatted_tag_val)
            address += len(formatted_tag_val)

        hex_address = '%04x' % address
        hex_address = hex_address[2:4] + hex_address[0:2]
        self.command('WHS', hex_address + 'HSE')
