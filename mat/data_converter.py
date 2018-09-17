from mat.data_file_factory import create_data_file
from mat.data_file import output_factory


DEFAULT_PARAMETERS = {
    'output_type': 'discrete',
    'output_format': 'csv',
    'average': True
}


class DataConverter:
    def __init__(self, path, **kwargs):
        self.path = path
        self.parameters = DEFAULT_PARAMETERS
        self.parameters.update(kwargs)
        self.outputs = None
        self._source_file = None

    def source_file(self):
        if self._source_file:
            return self._source_file
        self._source_file = create_data_file(self.path)
        return self._source_file

    def convert(self):
        self.outputs = self._open_outputs()
        for i in range(self.source_file().n_pages()):
            page = self.source_file().load_page(i)
            pass
            # for outputters in outputs:
            #     outputters.write_sensor_data(page)

    def _open_outputs(self):
        return output_factory(self.source_file().sensors(),
                              self.parameters)

    def __del__(self):
        if self._source_file:
            self._source_file.close()
