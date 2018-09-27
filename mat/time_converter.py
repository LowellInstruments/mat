from datetime import datetime
from abc import ABC, abstractmethod


def create_time_converter(time_format):
    time_converters = {'iso8601': Iso8601,
                       'legacy': Legacy,
                       'posix': Posix}
    return time_converters.get(time_format)


class TimeConverter(ABC):
    @abstractmethod
    def header_str(self):
        pass

    @abstractmethod
    def convert(self, posix_time):
        pass


class Iso8601(TimeConverter):
    def header_str(self):
        return 'ISO 8601 Time'

    def convert(self, posix_time):
        time = datetime.utcfromtimestamp(float(posix_time))
        return time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]


class Legacy(TimeConverter):
    def header_str(self):
        return 'Date,Time'

    def convert(self, posix_time):
        time = datetime.utcfromtimestamp(float(posix_time))
        return time.strftime('%Y-%m-%d,%H:%M:%S.%f')[:-3]


class Posix(TimeConverter):
    def header_str(self):
        return 'POSIX Time'

    def convert(self, posix_time):
        return '{:.3f}'.format(float(posix_time))
