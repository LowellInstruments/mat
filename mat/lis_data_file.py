from mat.sensor_data_file import SensorDataFile
from datetime import datetime
from mat.header import START_TIME
from mat.utils import epoch


DATA_START = 1024


class LisDataFile(SensorDataFile):
    def n_pages(self):
        return 1

    def load_page(self, i):
        pass

    def page_times(self):
        start_time = self.header().tag(START_TIME)
        page_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        return epoch(page_time)

    def mini_header_length(self):
        return 0

    def data_start(self):
        return DATA_START
