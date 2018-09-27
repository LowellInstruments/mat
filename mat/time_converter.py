from datetime import datetime
from abc import ABC, abstractmethod
import numpy as np


def create_time_converter(time_format):
    time_converters = {'iso8601': Iso8601,
                       'legacy': Legacy,
                       'posix': Posix}
    return time_converters.get(time_format)()


class TimeConverter(ABC):
    def __init__(self):
        self.converter = np.vectorize(lambda t: self._process(t))

    @abstractmethod
    def header_str(self):
        pass

    @abstractmethod
    def _process(self, posix_time):
        pass

    def _format_time(self, posix_time, time_format):
        time = datetime.utcfromtimestamp(float(posix_time))
        return time.strftime(time_format)

    def convert(self, posix_time):
        return self.converter(posix_time)


class Iso8601(TimeConverter):
    def header_str(self):
        return 'ISO 8601 Time'

    def _process(self, posix_time):
        time_str = self._format_time(posix_time, '%Y-%m-%dT%H:%M:%S.%f')
        return time_str[:-3]


class Legacy(TimeConverter):
    def header_str(self):
        return 'Date,Time'

    def _process(self, posix_time):
        time_str = self._format_time(posix_time, '%Y-%m-%d,%H:%M:%S.%f')
        return time_str[:-3]


class Posix(TimeConverter):
    def header_str(self):
        return 'POSIX Time'

    def _process(self, posix_time):
        return '{:.3f}'.format(float(posix_time))
