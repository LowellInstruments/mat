from mat.sensor_data_file import SensorDataFile


DATA_START = 32768
PAGE_SIZE = 1024**2


class LidDataFile(SensorDataFile):
    extension = ".lid"

    def _calc_n_pages(self):
        n_pages = 0
        while True:
            target = DATA_START + PAGE_SIZE * n_pages
            self.file().seek(target)
            this_line = self.file().readline().decode('IBM437')
            if this_line == '':
                return n_pages
            if this_line.startswith('MHS'):
                n_pages += 1
            else:
                raise ValueError
