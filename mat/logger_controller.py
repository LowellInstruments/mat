# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

import datetime
import os
import re
import numpy as np
from serial import (
    Serial,
    SerialException,
)
from serial.tools.list_ports import grep
from mat.converter import Converter
from mat.calibration_factories import make_from_string
from mat.logger_cmd import LoggerCmd


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
            self.logger_info = self.__parse_li(li_string)

    def get_timestamp(self):
        """ Return posix timestamp """
        date_string = self.command(TIME_CMD)
        epoch = datetime.datetime(1970, 1, 1)  # naive datetime format
        logger_time = datetime.datetime.strptime(date_string,
                                                 '%Y/%m/%d %H:%M:%S')
        return (logger_time-epoch).total_seconds()

    def get_logger_settings(self):
        gls_string = self.command(LOGGER_SETTINGS_CMD)
        logger_settings = {}
        if not gls_string:
            return {}

        if gls_string[0:2] == '01':
            logger_settings['TMP'] = True
        else:
            logger_settings['TMP'] = False

        if gls_string[2:4] == '01':
            logger_settings['ACL'] = True
        else:
            logger_settings['ACL'] = False

        if gls_string[4:6] == '01':
            logger_settings['MGN'] = True
        else:
            logger_settings['MGN'] = False

        tri_hex = gls_string[8:10] + gls_string[6:8]
        tri_int = int(tri_hex, 16)
        logger_settings['TRI'] = tri_int

        ori_hex = gls_string[12:14] + gls_string[10:12]
        ori_int = int(ori_hex, 16)
        logger_settings['ORI'] = ori_int

        bmr_hex = gls_string[14:16]
        bmr_int = int(bmr_hex, 16)
        logger_settings['BMR'] = bmr_int

        bmn_hex = gls_string[18:20] + gls_string[16:18]
        bmn_int = int(bmn_hex, 16)
        logger_settings['BMN'] = bmn_int

        if len(gls_string) == 30:
            logger_settings['PRS'] = gls_string[20:22] == '01'
            logger_settings['PHD'] = gls_string[22:24] == '01'
            logger_settings['PRR'] = int(gls_string[24:26], 16)
            logger_settings['PRN'] = int(gls_string[28:30] + gls_string[26:28],
                                         16)

        return logger_settings

    def stop_with_string(self, data):
        return self.command(STOP_WITH_STRING_CMD, data)

    def get_sensor_readings(self):
        sensor_string = self.command(SENSOR_READINGS_CMD)
        return self._parse_sensors(sensor_string)

    def get_sd_capacity(self):
        data = self.command(SD_CAPACITY_CMD)
        if not data:
            return None

        regexp = re.search('([0-9]+)KB', data)
        if regexp:
            return int(regexp.group(1))
        else:
            return None

    def get_sd_free_space(self):
        data = self.command(SD_FREE_SPACE_CMD)
        if not data:
            return None

        regexp = re.search('([0-9]+)KB', data)
        if regexp:
            return int(regexp.group(1))
        else:
            return None

    def get_sd_file_size(self):
        fsz = self.command(SD_FILE_SIZE_CMD)
        return int(fsz) if fsz else None

    def __parse_li(self, li_string):
        logger_info = {}
        try:
            tag = li_string[0:2]
            while tag != '##' and tag != '\xff' * 2:
                length = ord(li_string[2])
                value = li_string[3:3 + length]
                if tag == 'CA':
                    value = value[2:4] + value[0:2]
                    value = int(value, 16)
                    if value > 32768:
                        value -= 65536
                    value /= float(256)  # float() is to avoid integer division
                elif tag == 'BA' or tag == 'DP':
                    if length == 4:
                        value = value[2:4] + value[0:2]
                        value = int(value, 16)
                    else:
                        value = 0
                logger_info[tag] = value
                li_string = li_string[3 + length:]
                tag = li_string[0:2]
        except (IndexError, ValueError):
            logger_info = {'error': True}
        return logger_info

    def _parse_sensors(self, data):
        channels = []
        if not data or not (len(data) == 32 or len(data) == 40):
            return None

        n_sensors = 8 if len(data) == 32 else 10
        for i in range(n_sensors):
            dataHex = data[i * 4:i * 4 + 4]
            dataHex = dataHex[2:4] + dataHex[0:2]
            dataInt = int(dataHex, 16)
            # Convert to negative unless temperature or pressure
            if i not in [0, 8]:
                if dataInt > 32768:
                    dataInt -= 65536
            channels.append(dataInt)

        temp_raw = channels[0]
        accel_raw = np.array([[channels[1]], [channels[2]], [channels[3]]])
        mag_raw = np.array([[channels[4]], [channels[5]], [channels[6]]])
        batt = np.array([float(channels[7]) / 1000])

        if n_sensors == 10:
            pressure_raw = channels[8]
            pressure = self.converter.pressure(pressure_raw)[0]
            light_raw = channels[9]
            light = self.converter.light(np.array([light_raw]))

        else:
            light_raw = 0
            light = 0
            pressure_raw = 0
            pressure = 0

        if temp_raw == 0:  # Avoid 0 right after power up
            temp_raw = 1

        temp = self.converter.temperature(temp_raw)
        accel = self.converter.accelerometer(accel_raw)
        mag = self.converter.magnetometer(mag_raw, np.array([temp]))

        sensors = {}
        sensors['temp_raw'] = temp_raw
        sensors['temp'] = temp

        sensors['ax_raw'] = accel_raw[0]
        sensors['ax'] = accel[0]

        sensors['ay_raw'] = accel_raw[1]
        sensors['ay'] = accel[1]

        sensors['az_raw'] = accel_raw[2]
        sensors['az'] = accel[2]

        sensors['mx_raw'] = mag_raw[0]
        sensors['mx'] = mag[0]

        sensors['my_raw'] = mag_raw[1]
        sensors['my'] = mag[1]

        sensors['mz_raw'] = mag_raw[2]
        sensors['mz'] = mag[2]

        sensors['batt'] = batt
        sensors['light_raw'] = light_raw
        sensors['light'] = light

        sensors['pressure'] = pressure
        sensors['pressure_raw'] = pressure_raw
        return sensors

    def sync_time(self):
        datetimeObj = datetime.datetime.now()
        formattedString = datetimeObj.strftime('%Y/%m/%d %H:%M:%S')
        return self.command(SYNC_TIME_CMD, formattedString)

    def set_callback(self, event, callback):
        self.__callback[event] = callback

    def __del__(self):
        self.close()
