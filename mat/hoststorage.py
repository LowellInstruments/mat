"""
Read/write hoststorage data from a logger or file

There have been several different iterations of calibration coefficients since the introduction of the MAT logger.
This module is responsible for managing how the various versions are read and written

V2Hoststorage is represented in the logger in the following way:
3 letter tag, 1 hex number for length, ascii numeric value
eg. AXX61.1201  --  AXX is the tag, 6 is the length of data that follows, 1.1201 is the value

V3Hoststorage is encoded as ascii85 which encodes a 4-byte float as five printable characters
"""

from abc import ABC, abstractclassmethod, abstractmethod
from mat import ascii85
import re



def load_from_file(file_path):
    """
    Create a calibration object based on a host storage text file.
    NOTE: this is from a host storage text file created during calibration.
    """
    with open(file_path, 'r') as fid:
        hs_dict = {}
        for line in fid:
            line = line.strip()
            if line.startswith('//'):  # remove comments at start of file
                continue
            if len(line) == 0:  # blank line (usually at end of file)
                continue
            if line.find('//', 9) != -1:  # remove inline comments
                line = line[:line.find('//', 9)].strip()
            tag_value = line.split(' ')
            assert len(tag_value) == 2, 'Structure error in host storage file.'
            hs_dict[tag_value[0]] = tag_value[1]

    if 'RVN' not in hs_dict.keys():
        hs_dict['RVN'] = '2'
    class_ = {'2': V2Hoststorage, '3': V3Hoststorage}.get(hs_dict['RVN'])
    return class_(hs_dict)


def load_from_string(hs_string):
    """
    Factory function to return correct calibration subclass based on a string
    hs_string --  the host storage string from a lid or lis file, or the string returned from the RHS command.
    """

    # It's okay if the string is empty or all 255s. Create a default V2 host storage
    if not hs_string or all([c == 255 for c in bytes(hs_string, encoding='IBM437')]):
        return V2Hoststorage({})

    if hs_string and not hs_string.startswith('HSS'):
        raise ValueError('Host storage string must begin with HSS')

    if hs_string.startswith('HSSRVN13'):
        return V3Hoststorage.load_from_string(hs_string)
    else:
        return V2Hoststorage.load_from_string(hs_string)


def load_from_datafile(file_obj):
    """
    Create a calibration object from a data file (.lid/.lis)
    file_obj is an open .lid/.lis file in binary mode
    """
    file_pos = file_obj.tell()
    file_obj.seek(0)
    assert file_obj.mode == 'rb', 'File must be open for binary reading'
    this_line = file_obj.readline().decode('IBM437')
    while not this_line.startswith('HDE'):
        this_line = file_obj.readline().decode('IBM437')
    hs_str = file_obj.read(380)
    file_obj.seek(file_pos)
    return load_from_string(hs_str.decode('IBM437'))


class Hoststorage(ABC):
    def __init__(self, hs_dict):
        """
        hs_dict is passed to the subclasses with values as strings
        The subclasses must convert the string values to numeric values and pass them back to this __init__ method
        The V2 __init__ needs to convert plain text ascii to float
        The V3 __init__ needs to convert five ascii85 characters to float
        """
        if not hs_dict:
            hs_dict = self.load_generic()
            self.is_generic = True
        else:
            self.is_generic = False

        for tag in hs_dict:
            hs_dict[tag] = float(hs_dict[tag])
        self.hs_dict = hs_dict

    @abstractclassmethod
    def load_from_string(self, hs_string):
        pass

    @abstractmethod
    def format_for_file(self):
        pass

    @abstractmethod
    def format_for_write(self):
        pass

    def load_generic(self):
        hs_dict = {'AXX': 1, 'AXY': 0, 'AXZ': 0, 'AXC': 0, 'AXV': 0, 'AYX': 0, 'AYY': 1, 'AYZ': 0, 'AYC': 0,
                   'AYV': 0, 'AZX': 0, 'AZY': 0, 'AZZ': 1, 'AZC': 0, 'AZV': 0, 'RVN': 2, 'TMO': 0, 'TMR': 10000,
                   'TMA': 0.0011238100354, 'TMB': 0.0002349457073, 'TMC': 0.0000000848361,
                   'MXX': 1, 'MXY': 0, 'MXZ': 0, 'MXV': 0, 'MYX': 0, 'MYY': 1, 'MYZ': 0, 'MYV': 0,
                   'MZX': 0, 'MZY': 0, 'MZZ': 1, 'MZV': 0, 'PRA': 3, 'PRB': 0.0016,
                   'PHA': 0, 'PHB': 0}
        return hs_dict


class V2Hoststorage(Hoststorage):
    @classmethod
    def load_from_string(cls, hs_string):
        hs_dict = {}
        hs_string = hs_string[3:]
        tag = hs_string[:3]
        while tag != 'HSE':
            data_length = int(hs_string[3], 16)
            value = hs_string[4:4 + data_length]
            hs_dict[tag] = value
            hs_string = hs_string[4 + data_length:]
            tag = hs_string[0:3]
        return cls(hs_dict)

    def format_for_write(self):
        """
        This generator function formats the host storage dict for writing to the logger.
        """
        yield 'RVN12'  # Prior to V3, RVN didn't need to be first, but what the heck...
        for key in self.hs_dict:
            if key == 'RVN':
                continue
            # TODO this may need to be changed to a number of decimal points. e.g. %0.3f
            value = str(self.hs_dict[key]) # truncate to 15 characters (or less)
            length_hex = '%x' % len(value)  # hex length as an ascii character
            yield key + length_hex + value

    def format_for_file(self):
        yield 'RVN 2'
        for key in self.hs_dict:
            # handle the special cases
            if key == 'RVN':
                continue
            elif key in ['TMO', 'TMR']:
                value = '{:.0f}'.format(self.hs_dict[key])
            elif key in ['TMA', 'TMB', 'TMC']:
                value = '{:.11f}'.format(self.hs_dict[key])
            elif key in ['MXV', 'MYV', 'MZV']:
                value = '{:.1f}'.format(self.hs_dict[key])
            else:
                value = '{:.3f}'.format(self.hs_dict[key])
            if re.search('^[-0\.]+$', value):  # if the string is only zeros, save space and make it a single '0'
                value = '0'
            yield '{} {}'.format(key, value)


class V3Hoststorage(Hoststorage):
    """
    V3Hoststorage is encoded in ascii85
    """
    def __init__(self, hs_dict):
        for tag in hs_dict:
            if 'RVN' in tag:
                hs_dict[tag] = float(hs_dict[tag])
                continue
            hs_dict[tag] = ascii85.ascii85_to_num(hs_dict[tag])
        super().__init__(hs_dict)

    @classmethod
    def load_from_string(cls, hs_string):
        hs_dict = {}
        hs_dict['RVN'] = 3
        hs_string = hs_string[8:]
        tag = hs_string[:3]
        while tag != 'HSE':
            value = hs_string[3:8]
            hs_dict[tag] = value
            hs_string = hs_string[8:]
            tag = hs_string[0:3]
        return cls(hs_dict)

    def format_for_file(self):
        pass

    def format_for_write(self):
        """
        This generator function formats the host storage dict for writing to the logger.
        """
        yield 'RVN13'
        for key in self.hs_dict:
            if key == 'RVN':
                continue
            value = ascii85.num_to_ascii85(self.hs_dict[key])
            yield key + value

