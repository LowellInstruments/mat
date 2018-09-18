from mat.sensor_data_file import SensorDataFile
from math import ceil
from mat.utils import parse_tags, epoch
from datetime import datetime
import numpy as np


DATA_START = 32768
PAGE_SIZE = 1024**2


class LidDataFile(SensorDataFile):
    def n_pages(self):
        return ceil((self.file_size() - DATA_START) / PAGE_SIZE)

    def _load_page(self, i):
        if i >= self.n_pages():
            raise ValueError('page {} exceeds number of pages'.format(i))

        ind = (self.data_start() + (i * PAGE_SIZE) + self.mini_header_length())
        self._file.seek(ind)
        return np.fromfile(self.file(),
                           dtype='<i2',
                           count=self.samples_per_page())

    def data_start(self):
        return DATA_START

    def page_times(self):
        if self._page_times:
            return self._page_times
        page_start_times = []
        for page_n in range(self.n_pages()):
            header_string = self._read_mini_header(page_n)
            mini_header = parse_tags(header_string)
            time = mini_header['CLK']
            page_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            epoch_time = epoch(page_time)
            # The timestamp on all pages after the first have an
            # extra second (permanent firmware bug)
            if page_n > 0:
                epoch_time -= 1
            page_start_times.append(epoch_time)
        return page_start_times

    def _read_mini_header(self, page):
        file_position = self.file().tell()
        self.file().seek(DATA_START + PAGE_SIZE * page)
        header_string = self.file().read(self.mini_header_length())
        header_string = header_string.decode('IBM437')
        header_string = header_string[5:-5]  # remove HDE\r\n and HDS\r\n
        self.file().seek(file_position)
        return header_string

    def mini_header_length(self):
        if self._mini_header_length:
            return self._mini_header_length
        file_position = self.file().tell()
        self.file().seek(DATA_START)
        this_line = self.file().readline().decode('IBM437')
        if not this_line.startswith('MHS'):
            raise ValueError('MHS tag missing on first data page.')
        while not this_line.startswith('MHE'):
            this_line = self.file().readline().decode('IBM437')
        end_pos = self._file.tell()
        self.file().seek(file_position)
        self._mini_header_length = end_pos-DATA_START
        return self._mini_header_length
