from datetime import datetime
from abc import ABC, abstractmethod
from numpy import vectorize


def create_time_converter(time_format):
    time_converters = {'iso8601': Iso8601,
                       'legacy': Legacy,
                       'posix': Posix,
                       'elapsed': Elapsed}
    return time_converters.get(time_format)()


class TimeConverter(ABC):
    def __init__(self):
        self.converter = vectorize(lambda t: self._process(t))

    @abstractmethod
    def header_str(self):
        pass  # pragma: no cover

    @abstractmethod
    def _process(self, posix_time):
        pass  # pragma: no cover

    def _format_time(self, posix_time, time_format):
        time = datetime.utcfromtimestamp(float(posix_time))
        return time.strftime(time_format)

    def convert(self, posix_time):
        return self.converter(posix_time)


class Iso8601(TimeConverter):
    def header_str(self):
        return 'ISO 8601 Time'

    def _process(self, posix_time):
        column_header = self._format_time(posix_time, '%Y-%m-%dT%H:%M:%S.%f')
        return column_header[:-3]


class Legacy(TimeConverter):
    def header_str(self):
        return 'Date,Time'

    def _process(self, posix_time):
        column_header = self._format_time(posix_time, '%Y-%m-%d,%H:%M:%S.%f')
        return column_header[:-3]


class Posix(TimeConverter):
    def header_str(self):
        return 'POSIX Time'

    def _process(self, posix_time):
        return '{:.3f}'.format(float(posix_time))


class Elapsed:
    """
    Doesn't inherit from TimeConverter but has same interface
    """
    def __init__(self):
        self.converter = None
        self.start_time = None

    def header_str(self):
        return 'Elapsed Seconds'

    def _process(self, posix_time):
        return '{:.3f}'.format(float(posix_time) - self.start_time)

    def convert(self, posix_time):
        if self.converter is None:
            self.start_time = float(posix_time[0])
            self.converter = vectorize(lambda t: self._process(t))
        return self.converter(posix_time)
