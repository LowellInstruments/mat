# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

from mat.header import Header
from mat.calibration_factories import make_from_string
from mat.sensor import SensorFactory
from abc import ABC, abstractmethod
from math import floor
from mat.header import ORIENTATION_INTERVAL, TEMPERATURE_INTERVAL


FULL_HEADER_LENGTH = 1000
CALIBRATION_STRING_LENGTH = 380


class SensorDataFile(ABC):
    def __init__(self, file_path):
        self._file_path = file_path
        self._file = None
        self._n_pages = None
        self._header = None
        self._calibration = None
        self._page_times = None
        self._cached_page = None
        self._cached_page_n = None
        self._file_size = None
        self._mini_header_length = None
        self._samples_per_page = None

    @abstractmethod
    def data_start(self):
        pass  # pragma: no cover

    @abstractmethod
    def load_page(self, i):
        pass  # pragma: no cover

    @abstractmethod
    def mini_header_length(self):
        pass  # pragma: no cover

    @abstractmethod
    def n_pages(self):
        pass  # pragma: no cover

    @abstractmethod
    def page_times(self):
        pass  # pragma: no cover

    def page(self, i):
        if self._cached_page_n == i:
            return self._cached_page
        self._cached_page_n = i
        self._cached_page = self.load_page(i)
        return self._cached_page

    def header(self):
        if self._header:
            return self._header
        self._header = Header(self._read_full_header())
        self._header.parse_header()
        return self._header

    def calibration(self):
        if self._calibration:
            return self._calibration
        full_header = self._read_full_header()
        calibration_start = full_header.find('HDE\r\n')
        if calibration_start == -1:
            raise ValueError('HDE tag missing from header')
        start_ind = calibration_start + 5  # 5 chars for tag and /r/n
        end_ind = calibration_start + 5 + CALIBRATION_STRING_LENGTH
        self._calibration = make_from_string(full_header[start_ind:end_ind])
        return self._calibration

    def major_interval(self):
        orientation_interval = self.header().tag(ORIENTATION_INTERVAL) or 0
        temperature_interval = self.header().tag(TEMPERATURE_INTERVAL) or 0
        return max(orientation_interval, temperature_interval)

    def seconds_per_page(self):
        if self.n_pages() > 1:
            return self.page_times()[1] - self.page_times()[0]
        else:
            return self._partial_page_seconds()

    def samples_per_page(self):
        return self._count_samples(self.sensors())

    def _count_samples(self, sensor_list):
        samples = 0
        for s in sensor_list:
            samples += s.samples_per_page()
        return samples

    def file(self):
        if self._file is None:
            self._file = open(self._file_path, 'rb')
        return self._file

    def sensors(self):
        return SensorFactory(self.header(),
                             self.calibration(),
                             self.seconds_per_page()).get_sensors()

    def file_size(self):
        if self._file_size:
            return self._file_size
        file_pos = self.file().tell()
        self.file().seek(0, 2)
        self._file_size = self.file().tell()
        self.file().seek(file_pos)
        return self._file_size

    def _partial_page_seconds(self):
        # create a temporary set of sensors and tell them the page is equal
        # to the major interval. Then query each sensor to get the total
        # number of samples.

        maj_interval = self.major_interval()
        sensors = SensorFactory(self.header(),
                                self.calibration(),
                                maj_interval).get_sensors()

        n_samples_per_interval = self._count_samples(sensors)
        remaining_bytes = (self.file_size()
                           - self.data_start()
                           - self.mini_header_length())
        samples = floor(remaining_bytes/2)
        n_intervals = floor(samples / n_samples_per_interval)
        return n_intervals * self.major_interval()

    def _read_full_header(self):
        file_position = self.file().tell()
        self.file().seek(0)
        full_header = self.file().read(FULL_HEADER_LENGTH).decode('IBM437')
        self.file().seek(file_position)
        return full_header

    def close(self):
        if self._file:
            self._file.close()
        self._file = None

    def __del__(self):
        if self._file:
            self.close()
