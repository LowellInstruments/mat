# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

import datetime
import os
import re
from serial import (
    Serial,
    SerialException,
)
from serial.tools.list_ports import grep
from mat.calibration_factories import make_from_string
from mat.converter import Converter
from mat.logger_cmd import LoggerCmd
from mat.logger_info_parser import LoggerInfoParser
from mat.sensor_parser import SensorParser
from mat.utils import four_byte_int


# TODO: the "command" method is in DIRE shape! Please, please fix it!
# TODO: currently the logger class is blocking. Needs to be rewritten
# TODO: if host storage isn't loaded, gsr crashes.
# TODO: A default value needs to be loaded.

FIRMWARE_VERSION_CMD = 'GFV'
HOST_STORAGE_CMD = 'RHS'
INTERVAL_TIME_CMD = 'GIT'
LOGGER_INFO_CMD = 'RLI'
LOGGER_SETTINGS_CMD = 'GLS'
PAGE_COUNT_CMD = 'GPC'
RESET_CMD = 'RST'
RUN_CMD = 'RUN'
SD_CAPACITY_CMD = 'CTS'
SD_FILE_SIZE_CMD = 'FSZ'
SD_FREE_SPACE_CMD = 'CFS'
SENSOR_READINGS_CMD = 'GSR'
SERIAL_NUMBER_CMD = 'GSN'
START_TIME_CMD = 'GST'
STATUS_CMD = 'STS'
STOP_CMD = 'STP'
STOP_WITH_STRING_CMD = 'SWS'
SYNC_TIME_CMD = 'STM'
TIME_CMD = 'GTM'

SIMPLE_CMDS = [
    FIRMWARE_VERSION_CMD,
    INTERVAL_TIME_CMD,
    PAGE_COUNT_CMD,
    RUN_CMD,
    SERIAL_NUMBER_CMD,
    START_TIME_CMD,
    STATUS_CMD,
    STOP_CMD,
    TIME_CMD,
]


PORT_PATTERNS = {
    'posix': r'(ttyACM0)',
    'nt': r'^COM(\d+)',
}


TIMEOUT = 5


def find_port():
    field = grep('2047:08[AEae]+')[0][0]
    pattern = PORT_PATTERNS.get(os.name)
    if not pattern:
        raise RuntimeError("Unsupported operating system: " + os.name)
    return re.search(pattern, field).group(1)


class LoggerController(object):
    def __init__(self):
        self.is_connected = False
        self.__port = None
        self.com_port = None
        self.__callback = {}
        self.logger_info = {}
        self.hoststorage = None
        self.converter = None

    def open_port(self, com_port=None):
        com_port = com_port or find_port()
        try:
            if com_port:
                self._open_port(com_port)
        except SerialException:
            self.close()
        return self.is_connected

    def _open_port(self, com_port):
        if isinstance(self.__port, Serial):
            self.__port.close()
        if os.name == 'posix':
            self.__port = Serial('/dev/' + com_port)
        else:
            self.__port = Serial('COM' + str(com_port))
        self.__port.timeout = TIMEOUT
        self.is_connected = True
        self.com_port = com_port

    def command(self, *args):
        if not self.is_connected:
            return None
        try:
            return self.find_tag(self.target_tag(args))
        except SerialException:
            self.close()
            return None

    def find_tag(self, target):
        if not target:
            return
        while True:
            cmd = LoggerCmd(self.__port)
            if cmd.tag == target or cmd.tag == 'ERR':
                self.callback('rx', cmd.cmd_str())
                return cmd.result()

    def callback(self, key, cmd_str):
        if key in self.__callback:
            self.__callback[key](cmd_str)

    def target_tag(self, args):
        tag = args[0]
        data = ''
        if len(args) == 2:
            data = str(args[1])
        length = '%02x' % len(data)
        if tag == 'sleep' or tag == 'RFN':
            out_str = tag + chr(13)
        else:
            out_str = tag + ' ' + length + data + chr(13)
        self.__port.reset_input_buffer()
        self.__port.write(out_str.encode('IBM437'))
        self.callback('tx', out_str[:-1])
        if tag == RESET_CMD or tag == 'sleep' or tag == 'BSL':
            return ''
        return tag

    def close(self):
        if self.__port:
            self.__port.close()
        self.is_connected = False
        self.com_port = 0

    def load_host_storage(self):
        read_size = 38
        hs_string = ''

        # Load the entire HS from the logger
        for i in range(10):
            read_address = i * read_size
            read_address = '%04X' % read_address
            read_address = read_address[2:4] + read_address[0:2]
            read_length = '%02X' % read_size
            command_str = read_address + read_length
            in_str = self.command(HOST_STORAGE_CMD, command_str)
            if in_str:
                hs_string += in_str
            else:
                break

        self.hoststorage = make_from_string((hs_string))
        self.converter = Converter(self.hoststorage)

    def load_logger_info(self):
        read_size = 42
        li_string = ''
        for i in range(3):
            read_address = i*read_size
            read_address = '%04x' % read_address
            read_address = read_address[2:4] + read_address[0:2]
            read_length = '%02x' % read_size
            command_str = read_address + read_length
            li_string += self.command(LOGGER_INFO_CMD, command_str)
        if li_string and not all([c == 255 for c in
                                  bytes(li_string, encoding='IBM437')]):
            self.logger_info = LoggerInfoParser(li_string).info()

    def get_timestamp(self):
        """ Return posix timestamp """
        date_string = self.command(TIME_CMD)
        epoch = datetime.datetime(1970, 1, 1)  # naive datetime format
        logger_time = datetime.datetime.strptime(date_string,
                                                 '%Y/%m/%d %H:%M:%S')
        return (logger_time-epoch).total_seconds()

    def get_logger_settings(self):
        gls_string = self.command(LOGGER_SETTINGS_CMD)
        if not gls_string:
            return {}
        logger_settings = {
            'TMP': gls_string[0:2] == '01',
            'ACL': gls_string[2:4] == '01',
            'MGN': gls_string[4:6] == '01',
            'TRI': four_byte_int(gls_string[6:10]),
            'ORI': four_byte_int(gls_string[10:14]),
            'BMR': int(gls_string[14:16], 16),
            'BMN': four_byte_int(gls_string[16:20]),
        }

        if len(gls_string) == 30:
            logger_settings.update({
                'PRS': gls_string[20:22] == '01',
                'PHD': gls_string[22:24] == '01',
                'PRR': int(gls_string[24:26], 16),
                'PRN': four_byte_int(gls_string[26:30]),
            })

        return logger_settings

    def stop_with_string(self, data):
        return self.command(STOP_WITH_STRING_CMD, data)

    def get_sensor_readings(self):
        sensor_string = self.command(SENSOR_READINGS_CMD)
        # Should ensure that self.converter has been initialized
        return SensorParser(sensor_string, self.converter).sensors()

    def get_sd_capacity(self):
        return _extract_sd_kb(self.command(SD_CAPACITY_CMD))

    def get_sd_free_space(self):
        return _extract_sd_kb(self.command(SD_FREE_SPACE_CMD))

    def get_sd_file_size(self):
        fsz = self.command(SD_FILE_SIZE_CMD)
        return int(fsz) if fsz else None

    def sync_time(self):
        datetimeObj = datetime.datetime.now()
        formattedString = datetimeObj.strftime('%Y/%m/%d %H:%M:%S')
        return self.command(SYNC_TIME_CMD, formattedString)

    def set_callback(self, event, callback):
        self.__callback[event] = callback

    def __del__(self):
        self.close()


def _extract_sd_kb(data):
    if not data:
        return None
    regexp = re.search('([0-9]+)KB', data)
    if regexp:
        return int(regexp.group(1))
    else:
        return None
