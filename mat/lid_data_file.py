from mat.sensor_data_file import SensorDataFile
from math import ceil
from mat.utils import parse_tags, epoch, write_sws_file, consecutive_numbers
from datetime import datetime
import numpy as np


STOP_WITH_STRING_MARKER = -258


class LidDataFile(SensorDataFile):
    PAGE_SIZE = 1024 ** 2

    @property
    def data_start(self):
        return self.header().tag('DFS') or 32768

    def n_pages(self):
        if self._n_pages is not None:
            return self._n_pages
        ideal_n = ceil((self.file_size() - self.data_start) / self.PAGE_SIZE)
        successful_reads = 0
        try:
            for n in range(ideal_n):
                self._mini_headers.append(self._read_mini_header(n))
                successful_reads += 1
        except ValueError:
            self.header_error = (successful_reads, ideal_n)
        self._n_pages = successful_reads
        return self._n_pages

    def _load_page(self, i):
        if i >= self.n_pages():
            raise ValueError('page {} exceeds number of pages'.format(i))

        ind = (self.data_start
               + (i * self.PAGE_SIZE) + self.mini_header_length())
        self._file.seek(ind)
        data = np.fromfile(
            self.file(),
            dtype='<i2',
            count=(self.PAGE_SIZE-self.mini_header_length())//2)
        if i == self.n_pages()-1:
            stop_idx = consecutive_numbers(data, STOP_WITH_STRING_MARKER, 7)
            if stop_idx < len(data):
                write_sws_file(self._file_path.replace('.lid', '.gps'),
                               data[stop_idx+7:])
            data = data[:stop_idx]
        return data

    def page_times(self):
        if self._page_times:
            return self._page_times
        page_start_times = []
        for page_n in range(self.n_pages()):
            time = self._mini_headers[page_n]['CLK']
            page_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            epoch_time = epoch(page_time)
            # The timestamp on all pages after the first have an
            # extra second (permanent firmware bug)
            if page_n > 0:
                epoch_time -= 1
            page_start_times.append(int(epoch_time))
        self._page_times = page_start_times
        return self._page_times

    def page_voltages(self):
        voltages = []
        for page_n in range(self.n_pages()):
            voltage_hex = self._mini_headers[page_n]['BAT']
            voltages.append(int(voltage_hex, 16)/1000)
        return voltages

    def _read_mini_header(self, page):
        file_position = self.file().tell()
        self.file().seek(self.data_start + self.PAGE_SIZE * page)
        header_string = self.file().read(self.mini_header_length())
        self.file().seek(file_position)
        header_string = header_string.decode('IBM437')
        if not header_string.startswith('MHS'):
            raise ValueError('MHS tag missing from mini-header')
        header_string = header_string[5:-5]  # remove HDE\r\n and HDS\r\n
        return parse_tags(header_string)

    def mini_header_length(self):
        if self._mini_header_length:
            return self._mini_header_length
        file_position = self.file().tell()
        self.file().seek(self.data_start)
        this_line = self.file().readline().decode('IBM437')
        if not this_line.startswith('MHS'):
            raise ValueError('MHS tag missing on first data page.')
        while not this_line.startswith('MHE'):
            this_line = self.file().readline().decode('IBM437')
        end_pos = self._file.tell()
        self.file().seek(file_position)
        self._mini_header_length = end_pos-self.data_start
        return self._mini_header_length
