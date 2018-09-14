"""
This class should work something like this

open a lid file
load a data page
extract each sensor's data from the data page
apply the calibration to each sensor
write the calibrated data to an output file
"""


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
        # for i in range(data_source.n_pages()):
        #     page = data_source.load_page(i)
        #
        #     for outputters in outputs:
        #         outputters.write_sensor_data(page)

    def _open_outputs(self):
        return output_factory(self.source_file().sensors().sensors(),
                              self.parameters)

    def __del__(self):
        if self._source_file:
            self._source_file.close()
