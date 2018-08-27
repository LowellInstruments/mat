import serial
import serial.tools.list_ports
import numpy as np
import re
import time
import os
from mat import hoststorage, converter
import datetime


# TODO the "command" method is in DIRE shape! Please, please fix it!
# TODO currently the logger class is blocking. It needs to be rewritten in a non-block manner
# TODO if host storage isn't loaded, gsr crashes. A default value needs to be loaded.


class Logger(object):
    def __init__(self):
        self.printTx = False
        self.printRx = False
        self.__connected = False
        self.__port = None
        self.timeout = 6
        self.com_port = None
        self.__callback = {}
        self.printIO = False
        self.logger_info = {}
        self.hoststorage = None  # an object that holds the host storage values and performs sensor conversion
        self.converter = None

    def check_ports(self):
        port_info = serial.tools.list_ports.grep('2047:08[AEae]+')
        com_ports = []
        for this_port in port_info:
            for field in this_port:
                if os.name == 'posix':
                    port_re = re.search('(ttyACM0)', field)
                elif os.name == 'nt':
                    port_re = re.search('^COM(\d+)', field)
                else:
                    raise RuntimeError('Unsupported operating system')

                if port_re:
                    com_ports.append(port_re.group(1))

        return com_ports

    def open_port(self, com_port):
        try:
            if isinstance(self.__port, serial.Serial):
                self.__port.close()
            if os.name == 'posix':
                self.__port = serial.Serial('/dev/' + com_port, 9600)
            elif os.name == 'nt':
                self.__port = serial.Serial('COM' + str(com_port))

            self.__port.timeout = 5
            self.__connected = True
            self.com_port = com_port
        except:
            self.__connected = False
            self.close()

        # port_poller = threading.Thread(target=self.__port_watcher)
        # port_poller.start()
        return self.__connected

    # def __port_watcher(self):
    #     while self.__connected:
    #         if self.com_port not in self.check_ports():
    #             self.close()
    #             print 'Logger Disconnected'
    #             raise RuntimeError('Logger disconnected.')
    #         time.sleep(0.5)

    def auto_connect(self):
        ports = self.check_ports()
        if ports:
            state = self.open_port(ports[0])
        else:
            state = False
        return state

    def command(self, *args):
        return_val = None
        tag = args[0]
        data = ''
        if len(args) == 2:
            data = str(args[1])
        length = '%02x' % len(data)
        if not self.__connected:
            return

        try:
            if tag == 'sleep' or tag == 'RFN':
                out_str = tag + chr(13)
            else:
                out_str = tag + ' ' + length + data + chr(13)

            last_tx = time.time()
            self.__port.reset_input_buffer()

            self.__port.write(out_str.encode('IBM437'))

            if 'tx' in self.__callback:
                self.__callback['tx'](out_str[:-1])

            # RST, BSL and sleep don't return tags. This will allow the tx below to run and fail
            if tag == 'RST' or tag == 'sleep' or tag == 'BSL':
                tag_waiting = ''
            else:
                tag_waiting = tag

            while tag_waiting:
                # time.sleep(0.005)
                # if time.time() - last_tx > self.timeout:
                #     print 'Logger timeout. Waiting for: ' + tag_waiting
                #     self.close()
                #     break

                # flush out the nl and cr chars that inevitably end up coming first...

                inchar = self.__port.read(1).decode('IBM437')
                while ord(inchar) in [10, 13]:
                    inchar = self.__port.read(1).decode('IBM437')

                inline = inchar + self.__port.read(5).decode('IBM437')

                #TODO consider returning data as bytes type??? I don't know what is better...

                tag = inline[0:3]
                length = int(inline[4:6], 16)

                data = self.__port.read(length).decode('IBM437')

                if length != len(data):
                    raise RuntimeError(
                        'Incorrect data length. Expecting ' + str(length) + ' received ' + str(len(data)))

                if tag == tag_waiting:
                    if self.printIO:
                        print('RX: ' + tag + ' ' + inline[4:6] + data)
                    tag_waiting = ''
                    if 'rx' in self.__callback:
                        self.__callback['rx'](tag + ' ' + inline[4:6] + data)
                    return data
                elif tag == 'ERR':
                    tag_waiting = ''
                    if 'rx' in self.__callback:
                        self.__callback['rx'](tag + ' ' + inline[4:6] + data)
                    return None

        except serial.SerialException:
            print('Serial Exception')
            self.close()
            return None

    def close(self):
        if self.__port:
            self.__port.close()
        self.__connected = False
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
            in_str = self.command('RHS', command_str)
            if in_str:
                hs_string += in_str
            else:
                print('Logger returned empty string during HS read')
                break

        self.hoststorage = hoststorage.load_from_string((hs_string))
        self.converter = converter.Converter(self.hoststorage)

    def load_logger_info(self):
        read_size = 42
        li_string = ''
        for i in range(3):
            read_address = i*read_size
            read_address = '%04x' % read_address
            read_address = read_address[2:4] + read_address[0:2]
            read_length = '%02x' % read_size
            command_str = read_address + read_length
            li_string += self.command('RLI', command_str)

        # make sure a string was returned, and that all the characters weren't 255
        if li_string and not all([c == 255 for c in bytes(li_string, encoding='IBM437')]):
            self.logger_info = self.__parse_li(li_string)

    def get_time(self):
        return self.command('GTM')

    def get_timestamp(self):
        """ Return posix timestamp """
        date_string = self.command('GTM')
        epoch = datetime.datetime(1970, 1, 1)  # naive datetime format
        logger_time = datetime.datetime.strptime(date_string, '%Y/%m/%d %H:%M:%S')
        return (logger_time-epoch).total_seconds()

    def get_serial_number(self):
        return self.command('GSN')

    def get_firmware_version(self):
        return self.command('GFV')

    def get_interval_time(self):
        return self.command('GIT')

    def get_page_count(self):
        return self.command('GPC')

    def get_logger_settings(self):
        gls_string = self.command('GLS')
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
            logger_settings['PRS'] = True if gls_string[20:22] == '01' else False
            logger_settings['PHD'] = True if gls_string[22:24] == '01' else False
            logger_settings['PRR'] = int(gls_string[24:26], 16)
            logger_settings['PRN'] = int(gls_string[28:30] + gls_string[26:28], 16)

        return logger_settings

    def reset(self):
        self.command('RST')

    def get_status(self):
        return self.command('STS')

    def get_start_time(self):
        return self.command('GST')

    def run(self):
        self.command('RUN')

    def stop(self):
        self.command('STP')

    def stop_with_string(self, data):
        self.command('SWS', data)

    def is_connected(self):
        return self.__connected

    def get_sensor_readings(self):
        sensor_string = self.command('GSR')
        return self._parse_sensors(sensor_string)

    def get_sd_capacity(self):
        data = self.command('CTS')
        if not data:
            return None

        regexp = re.search('([0-9]+)KB', data)
        if regexp:
            return int(regexp.group(1))
        else:
            return None

    def get_sd_free_space(self):
        data = self.command('CFS')
        if not data:
            return None

        regexp = re.search('([0-9]+)KB', data)
        if regexp:
            return int(regexp.group(1))
        else:
            return None

    def get_sd_file_size(self):
        fsz = self.command('FSZ')
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
        except:
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
            # For all channels other than temperature and pressure, convert to negative number if necessary
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

        if temp_raw == 0:  # if the sensor doesn't report immediately after power up, causing a math error below
            print('Temperature sensor powerup error')
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
        self.command('STM', formattedString)

    def set_callback(self, event, callback):
        self.__callback[event] = callback

    def __del__(self):
        self.close()


