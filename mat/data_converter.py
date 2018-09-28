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
        self._is_running = None

    def source_file(self):
        if self._source_file:
            return self._source_file
        self._source_file = load_data_file(self.path)
        return self._source_file

    def cancel_conversion(self):
        # TODO: Nathan, I'm not sure if this is thread safe. This method
        # would be called from another thread running in Logger. I suspect
        # this may need to be done another way??
        self._is_running = False  # pragma: no cover

    def convert(self):
        self._is_running = True
        outputs = self.get_outputs(self.source_file().sensors(),
                                   self.parameters)
        page_times = self.source_file().page_times()
        for i in range(self.source_file().n_pages()):
            if not self._is_running:
                break  # pragma: no cover
            page = self.source_file().page(i)
            self._write_to_outputs(outputs, page, page_times[i])
            percent = (i + 1) / self.source_file().n_pages() * 100
            self._update_observers(percent)

    def _write_to_outputs(self, outputs, page, page_time):
        for this_output in outputs:
            this_output.process_page(page, page_time)

    def _update_observers(self, percent):
        for observer in self.observers:
            observer(percent)

    def get_outputs(self, sensors, parameters):
        return data_product_factory(sensors, parameters)

    def register_observer(self, observer):
        self.observers.append(observer)

    def __del__(self):
        if self._source_file:
            self._source_file.close()
