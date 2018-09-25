from mat.data_file_factory import load_data_file
from mat.data_product import data_product_factory
DEFAULT_PARAMETERS = {
    'output_directory': None,
    'output_type': 'discrete',
    'output_format': 'csv',
    'average': True,
    'time_format': 'iso8601'
}


class DataConverter:
    def __init__(self, path, **kwargs):
        self.path = path
        self.parameters = dict(DEFAULT_PARAMETERS)
        self.parameters.update(kwargs)
        self.parameters.update({'path': path})
        self._source_file = None
        self.observers = []

    def source_file(self):
        if self._source_file:
            return self._source_file
        self._source_file = load_data_file(self.path)
        return self._source_file

    def convert(self):
        outputs = self.get_outputs(self.source_file().sensors(),
                                   self.parameters)
        page_times = self.source_file().page_times()
        for i in range(self.source_file().n_pages()):
            page = self.source_file().page(i)
            for this_output in outputs:
                this_output.process_page(page, page_times[i])
            for observer in self.observers:
                observer((i+1) / self.source_file().n_pages() * 100)

    def get_outputs(self, sensors, parameters):
        return data_product_factory(sensors, parameters)

    def register_observer(self, observer):
        self.observers.append(observer)

    def __del__(self):
        if self._source_file:
            self._source_file.close()
