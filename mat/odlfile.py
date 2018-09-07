# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

"""
This module provides access to a lid/lis file
This includes:
Header
Host storage (calibration coefficients)
Full page reads

Usage:
Open a file for random binary read 'rb', using the "with" command
e.g. with open('myfile.lid', 'rb') as file_h
Pass the reference to the "load_file" function contained in this module.
This will return an object of the appropriate subclass depending on the
file type.

Basic file information is made available such as available channels, start
time, number of temp/pressure intervals, etc

It is the user's responsibility to calculate the sample time using page
start time and the time offset vectors
"""

# TODO LIS files need to assume a BMN of 1 when parsing! You can't use the
# header value
# TODO make sure methods that move the file cursor position return it after
# they are done

from mat import calibration
from mat.header import (
    Header,
    IS_ACCELEROMETER,
    IS_MAGNETOMETER,
    IS_PHOTO_DIODE,
    IS_PRESSURE,
    IS_TEMPERATURE,
    ORIENTATION_BURST_COUNT,
    ORIENTATION_BURST_RATE,
    ORIENTATION_INTERVAL,
    PRESSURE_BURST_COUNT,
    PRESSURE_BURST_RATE,
    TEMPERATURE_INTERVAL,
)
import numpy as np
import datetime
from abc import ABC, abstractmethod


def load_file(file_obj):
    """
    Factory to return the appropriate OdlFile subclass

    file_obj -- the handle of an open .lid or .lis file
    """
    try:
        extension = file_obj.name[-4:]
        class_ = {'.lid': LidFile, '.lis': LisFile}.get(extension)
    except KeyError:
        raise Exception('Invalid Filename')
    return class_(file_obj)


class OdlFile(ABC):
    """
    Abstract base class for interacting with a Lowell Instruments LID file.
    """

    def __init__(self, file_obj):
        self._file = file_obj
        self.file_size = self._file_size()
        header_str = file_obj.read(500).decode('IBM437')
        self.header = Header(header_str)
        self.header.parse_header()
        self.calibration = calibration.make_from_datafile(self._file)
        self.mini_header_length = self._mini_header_length()
        self.n_pages = self._n_pages()
        self.page_start_times = self._page_start_times()
        self.data_start = self._data_start()
        self.major_interval_seconds = max(self.header.temperature_interval,
                                          self.header.orientation_interval)

        sequence, interval_time_offset = self._build_sequence()

        self.maj_interval_bytes = len(sequence) * 2
        self.n_maj_intervals_per_page = self._n_maj_intervals_per_page()

        self.page_sequence = np.tile(sequence, self.n_maj_intervals_per_page)

        self.page_time_offset = (np.arange(self.n_maj_intervals_per_page) *
                                 self.major_interval_seconds)
        self.page_time_offset = np.tile(self.page_time_offset,
                                        (len(interval_time_offset), 1))
        self.page_time_offset = self.page_time_offset.T + interval_time_offset
        self.page_time_offset = np.reshape(self.page_time_offset, (-1,))

        self.samples_per_page = len(self.page_sequence)

        # logical index arrays for the various sensors
        self.is_temp = self.page_sequence == 'T'
        self.is_pres = self.page_sequence == 'P'
        self.is_light = self.page_sequence == 'L'
        self.is_accel = self.page_sequence == 'A'
        self.is_mag = self.page_sequence == 'M'
        self.end_time = 0
        self._cached_page = None
        self._cached_page_n = None

    def pressure(self):
        """ pressure values from the current page """
        pressure = self._cached_page[self.is_pres[:len(self._cached_page)]]
        return pressure.astype('uint16')

    def accelerometer(self):
        accel_index = self.is_accel[:len(self._cached_page)]
        accelerometer = self._cached_page[accel_index]
        # if this is the last page, check logging wasn't interrupted mid burst
        full_burst_end = (int(np.floor(len(accelerometer) /
                          (self.header.orientation_burst_count * 3))))
        full_burst_end *= self.header.orientation_burst_count * 3
        accelerometer = accelerometer[:full_burst_end]
        accelerometer = np.reshape(accelerometer, (3, -1), order='F')
        return accelerometer

    def magnetometer(self):
        mag_index = self.is_mag[:len(self._cached_page)]
        magnetometer = self._cached_page[mag_index]
        # if this is the last page, ckeck logging wasn't interrupted mid burst
        full_burst_end = (int(np.floor(len(magnetometer) /
                          (self.header.orientation_burst_count * 3))))
        full_burst_end *= self.header.orientation_burst_count * 3
        magnetometer = magnetometer[:full_burst_end]
        magnetometer = np.reshape(magnetometer, (3, -1), order='F')
        return magnetometer

    def temperature(self):
        temperature = self._cached_page[self.is_temp[:len(self._cached_page)]]
        return temperature.astype('uint16')

    def light(self):
        light = self._cached_page[self.is_light[:len(self._cached_page)]]
        return light.astype('uint16')

    def _build_sequence(self):
        """
        Position within major interval for temperature and orient intervals.

        Let's call this a "dead-reckoning" technique. Maybe not the most
        elegant, but it should be pretty understandable.

        TRI is the interval for: temperature, photodiode, and pressure sensor

        Light-sensor interval is tied to the TRI
        Pressure sensor interval is tied to TRI but it has it's own burst rate
        and number

        Byte ordering is as follows when samples occur at the same time:
        Temperature, Pressure, Light, Accelerometer, Magnetometer

        time_offset is measured in microseconds
        """

        h = self.header  # shorten things for the sake of easier reading
        major_interval_seconds = max(h.tag(TEMPERATURE_INTERVAL),
                                     h.tag(ORIENTATION_INTERVAL))

        # arrays to store the index values where samples begin
        sequence = []
        time_offset = []

        pres_remaining, accel_remaining, mag_remaining = 0, 0, 0

        # 'n' counts over the major interval by 64ths of seconds
        for n in range(0, major_interval_seconds * 64):
            # If TRI is the major interval, there will be multiple ORI
            # intervals within the major
            # and the counters will need resetting
            if (h.tag(ORIENTATION_INTERVAL) and n %
                    (h.tag(ORIENTATION_INTERVAL) * 64) == 0):
                accel_remaining = h.tag(ORIENTATION_BURST_COUNT) if \
                    h.tag(IS_ACCELEROMETER) else 0
                mag_remaining = h.tag(ORIENTATION_BURST_COUNT) if \
                    h.tag(IS_MAGNETOMETER) else 0
                pres_remaining = h.tag(PRESSURE_BURST_COUNT)

            if h.tag(IS_TEMPERATURE) and n % (h.tag(TEMPERATURE_INTERVAL) *
                                              64) == 0:
                sequence.append('T')
                time_offset.append(n)

            if h.tag(IS_PHOTO_DIODE) and n % (h.tag(TEMPERATURE_INTERVAL) *
                                              64) == 0:
                sequence.append('L')
                time_offset.append(n)

            # if pressure is enabled AND there are still samples in this burst
            # AND the time is right THEN
            if h.tag(IS_PRESSURE) and pres_remaining and n % \
                    (64 / h.tag(PRESSURE_BURST_RATE)) == 0:
                sequence.append('P')
                pres_remaining -= 1
                time_offset.append(n)

            if h.tag(IS_ACCELEROMETER) and accel_remaining and n % \
                    (64 / h.tag(ORIENTATION_BURST_RATE)) == 0:
                sequence.extend(['A', 'A', 'A'])
                accel_remaining -= 1
                time_offset.extend([n, n, n])

            if h.tag(IS_MAGNETOMETER) and mag_remaining and n % \
                    (64 / h.tag(ORIENTATION_BURST_RATE)) == 0:
                sequence.extend(['M', 'M', 'M'])
                mag_remaining -= 1
                time_offset.extend([n, n, n])

        return np.array(sequence), np.array(time_offset, dtype='float64') / 64

    def _file_size(self):
        """
        Size of the ODL file in bytes
        """

        file_pos = self._file.tell()
        self._file.seek(0, 2)
        file_length = self._file.tell()
        self._file.seek(file_pos)
        return file_length

    def __len__(self):
        return self.n_pages

    @abstractmethod
    def load_page(self, page_n):
        pass

    @abstractmethod
    def _mini_header_length(self):
        pass

    @abstractmethod
    def _n_pages(self):
        pass

    @abstractmethod
    def _page_start_times(self):
        pass

    @abstractmethod
    def _n_maj_intervals_per_page(self):
        pass

    @abstractmethod
    def _data_start(self):
        pass

    @abstractmethod
    def _end_time(self):
        """ time of last sample """
        pass


class LidFile(OdlFile):
    def __init__(self, file_obj):
        super(LidFile, self).__init__(file_obj)
        self.page_size = 1024 ** 2

    def load_page(self, page_n):
        """
        Loads a 1 MB data page (or remainder of the last page)
        """

        if page_n > self.n_pages:
            raise ValueError('page_n exceeds number of pages')

        data_start = (self.data_start + page_n * self.page_size +
                      self.mini_header_length)
        self._file.seek(data_start)
        self._cached_page = np.fromfile(self._file,
                                        dtype='<i2',
                                        count=self.samples_per_page)
        self._cached_page_n = page_n
        self._page_len = len(self._cached_page)

    def _end_time(self):
        pass
        # There was a bug in this code so it has been disabled for now
        # last_page_bytes = self.file_size - \
        #                   (32768+1024**2*(self.n_pages-1)) - \
        #                   self.mini_header_length - 1
        # last_page_samples = int(last_page_bytes/2)
        # return self.page_start_times[self.n_pages-1] + \
        #        self.page_time_offset[last_page_samples]

    def _data_start(self):
        return 32768

    def _mini_header_length(self):
        """
        See base class for documentation
        """

        self._file.seek(32768)  # jump to the start of the first data page
        this_line = self._file.readline().decode('IBM437')
        if not this_line.startswith('MHS'):
            raise LidError('MHS tag missing on first data page.')

        while not this_line.startswith('MHE'):
            this_line = self._file.readline().decode('IBM437')

        end_pos = self._file.tell()

        return end_pos-32768

    def _n_pages(self):
        """
        The number of data pages in the LID file.
        """
        n_pages = 0
        while True:
            self._file.seek(32768+1024**2*n_pages)
            this_line = self._file.readline().decode('IBM437')
            if this_line.startswith('MHS'):
                n_pages += 1
            else:
                break
        return n_pages

    def _page_start_times(self):
        """
        A list containing the start time of each data page.
        :return: list
        """
        epoch = datetime.datetime(1970, 1, 1)
        page_start_times = []
        for page_n in range(self.n_pages):
            self._file.seek(32768+1024**2*page_n)
            this_line = self._file.readline().decode('IBM437')
            if not this_line:  # tried reading for a non-existent page
                raise LidError('Page {} does not exist.'.format(page_n))
            if not this_line.startswith('MHS'):
                raise LidError('MHS tag missing on page {}.'.format(page_n))

            while True:  # Read until the CLK tag is reached
                this_line = self._file.readline().decode('IBM437')
                this_line = this_line.strip()
                tag, value = this_line[:3], this_line[4:]
                if tag == 'HSE':
                    raise LidError(
                        'CLK tag missing on page {}.'.format(page_n))
                if tag == 'CLK':
                    page_time = (datetime.datetime.strptime(
                        value, '%Y-%m-%d %H:%M:%S') - epoch).total_seconds()
                    # The timestamp on all pages after the first have an
                    # extra 1 second (permanent bug)
                    if page_n > 0:
                        page_time -= 1
                    page_start_times.append(page_time)
                    break  # tag found, move on to next page

        return page_start_times

    def _n_maj_intervals_per_page(self):
        """
        The number of major intervals per page
        """
        # Use the time stamp to avoid the firmware bug that stops writing early
        if self.n_pages > 1:
            seconds_per_page = int(self.page_start_times[1] -
                                   self.page_start_times[0])
            intervals_per_page, remainder = divmod(seconds_per_page,
                                                   self.major_interval_seconds)
            assert remainder == 0, 'Number of major intervals is not a ' \
                                   'factor of page time.'
        else:
            # This will be a little bigger than the data size.
            # It will be truncated in the parsing routine
            intervals_per_page = np.ceil((self.file_size-self.data_start) /
                                         self.maj_interval_bytes)

        return int(intervals_per_page)


class LisFile(OdlFile):
    def load_page(self, page_n):
        if page_n > 0:
            raise ValueError('page_n exceeds number of pages. '
                             '.lis file only has one data page')

        if page_n != self._cached_page_n:
            self._file.seek(self.data_start + self.mini_header_length)
            self._cached_page = np.fromfile(self._file,
                                            dtype='<i2',
                                            count=self.samples_per_page)
            self._cached_page_n = page_n

        return self._cached_page

    def _end_time(self):
        last_page_bytes = self.file_size - 1024
        last_page_samples = int(last_page_bytes/2)
        end_time = (self.page_start_times[0] +
                    self.page_time_offset[last_page_samples-1])
        return end_time

    def _data_start(self):
        return 1024

    def _mini_header_length(self):
        """
        Length of the mini header in bytes.
        :return: int
        """
        return 0

    def _n_pages(self):
        """
        The number of data pages in the LID file.
        :return: int
        """
        return 1

    def _page_start_times(self):
        """
        A list containing the start time of each data page
        """
        epoch = datetime.datetime(1970, 1, 1)
        page_time = datetime.datetime.strptime(self.header.start_time,
                                               '%Y-%m-%d %H:%M:%S')
        return [(page_time - epoch).total_seconds()]

    def _n_maj_intervals_per_page(self):
        return int(np.ceil((self.file_size-self.data_start) /
                           self.maj_interval_bytes))


class LidError(Exception):
    pass
