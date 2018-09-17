from mat.sensor_data_file import SensorDataFile


DATA_START = 32768
PAGE_SIZE = 1024**2


class LidDataFile(SensorDataFile):
    extension = ".lid"

    def _calc_n_pages(self):
        index = 0
        while True:
            page = self._nth_page(index)
            if page == '':
                return index
            if not page.startswith('MHS'):
                raise ValueError
            index += 1

    def _nth_page(self, index):
        target = DATA_START + PAGE_SIZE * index
        self.file().seek(target)
        return self.file().readline().decode('IBM437')
