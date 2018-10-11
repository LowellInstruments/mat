from mat.data_file_factory import load_data_file
from mat.data_product import data_product_factory


class ConversionParameters:
    def __init__(self, path, **kwargs):
        self.path = path
        self.output_directory = None
        self.output_type = 'discrete'
        self.output_format = 'csv'
        self.average = 'True'
        self.time_format = 'iso8601'
        self.tilt_curve = None
        self.declination = 0
        self._verify_kwargs(kwargs)
        self.__dict__.update(kwargs)

    def _verify_kwargs(self, kwargs):
        accepted_keys = self.__dict__.keys()
        if any([1 for x in kwargs if x not in accepted_keys]):
            raise ValueError('Unknown keyword')


class DataConverter:
    def __init__(self, parameters):
        self.parameters = parameters
        self.source_file = None
        self.observers = []
        self._is_running = None

    def _load_source_file(self):
        if self.source_file:
            return self.source_file
        self.source_file = load_data_file(self.parameters.path)
        return self.source_file

    def cancel_conversion(self):
        # TODO: Nathan, I'm not sure if this is thread safe. This method
        # would be called from another thread running in Logger. I suspect
        # this may need to be done another way??
        self._is_running = False  # pragma: no cover

    def convert(self):
        self._is_running = True
        self._load_source_file()
        outputs = data_product_factory(self.source_file.sensors(),
                                       self.parameters)
        page_times = self.source_file.page_times()
        for i in range(self.source_file.n_pages()):
            if not self._is_running:
                break  # pragma: no cover
            page = self.source_file.page(i)
            self._write_to_outputs(outputs, page, page_times[i])
            percent = (i + 1) / self.source_file.n_pages() * 100
            self._update_observers(percent)

    def _write_to_outputs(self, outputs, page, page_time):
        for this_output in outputs:
            this_output.process_page(page, page_time)

    def _update_observers(self, percent):
        for observer in self.observers:
            observer(percent_done=percent)

    def register_observer(self, observer):
        self.observers.append(observer)

    def __del__(self):
        if self.source_file:
            self.source_file.close()
