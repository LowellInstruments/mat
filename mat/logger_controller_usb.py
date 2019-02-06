# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

from mat.logger_controller import LoggerController
from mat.logger_controller import DELAY_COMMANDS
import os
import re
import time
from serial import (
    Serial,
    SerialException,
)
from serial.tools.list_ports import grep
from mat.logger_cmd import LoggerCmd


TIMEOUT = 5
PORT_PATTERNS = {
    'posix': r'(ttyACM0)',
    'nt': r'^COM(\d+)',
}


def find_port():
    try:
        field = list(grep('2047:08[AEae]+'))[0][0]
    except (TypeError, IndexError):
        raise RuntimeError("Unable to find port")
    pattern = PORT_PATTERNS.get(os.name)
    if not pattern:
        raise RuntimeError("Unsupported operating system: " + os.name)
    return re.search(pattern, field).group(1)


class LoggerControllerUSB(LoggerController):
    def __init__(self):
        super().__init__()
        self.is_connected = False
        self.__port = None
        self.com_port = None

    def open(self):
        self.open_port()

    def open_port(self, com_port=None):
        try:
            com_port = com_port or find_port()
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
            self.is_connected = False
            return None

    def find_tag(self, target):
        if not target:
            return
        while True:
            cmd = LoggerCmd(self.__port)
            wait_time = 0
            if cmd.tag in DELAY_COMMANDS:
                wait_time = 2
            if cmd.tag == target or cmd.tag == 'ERR':
                self.callback('rx', cmd.cmd_str())
                time.sleep(wait_time)
                return cmd.result()

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
        if tag == 'RST' or tag == 'sleep' or tag == 'BSL':
            return ''
        return tag

    def close(self):
        if self.__port:
            self.__port.close()
        self.is_connected = False
        self.com_port = 0
