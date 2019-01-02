from os import path
from .time_converter import create_time_converter


def output_stream_factory(file_path, parameters):
    output_types = {'csv': CsvStream}
    stream_class = output_types.get(parameters['output_format'])
    if stream_class is None:
        raise ValueError('Unknown output type' + parameters['output_format'])
    return stream_class(file_path, parameters)


class OutputStream:
    def __init__(self, file_path, parameters):
        self.file_path = file_path
        self.parameters = parameters
        self.streams = {}
        self.time_converter = create_time_converter(parameters['time_format'])

    def add_stream(self, data_product):
        pass  # pragma: no cover

    def set_column_header(self, stream, column_header):
        column_header = self.time_converter.header_str() + ',' + column_header
        self.streams[stream].column_header = column_header

    def set_data_format(self, stream, data_format):
        self.streams[stream].data_format = data_format

    def write(self, stream, data, time):
        time = self.time_converter.convert(time)
        self.streams[stream].write(data, time)


class CsvStream(OutputStream):
    def add_stream(self, data_product):
        self.streams[data_product] = CsvFile(self.file_path,
                                             data_product,
                                             self.parameters)


class CsvFile:
    EXTENSION = '.csv'

    def __init__(self, file_path, stream_name, parameters):
        self.file_path = file_path
        self.stream_name = stream_name
        self.parameters = parameters
        self.column_header = ''
        self.data_format = ''
        self.split = parameters['split'] or 100000
        self.write_count = 0

    def next_file_path(self):
        dir_name = path.dirname(self.file_path)
        destination = self.parameters['output_directory'] or dir_name
        file_prefix = path.basename(self.file_path).split('.')[0]
        file_num = self.write_count // self.split
        file_num_str = '_{}'.format(file_num) if self.split != 100000 else ''
        output_file_name = '{}_{}{}.csv'.format(file_prefix,
                                                self.stream_name,
                                                file_num_str)
        self.output_path = path.join(destination, output_file_name)

    def write_header(self):
        with open(self.output_path, 'w') as fid:
            fid.write(self.column_header + '\n')

    def write(self, data, time):
        if self.write_count % self.split == 0:
            self.next_file_path()
            self.write_header()

        data_format = '{},' + self.data_format + '\n'
        with open(self.output_path, 'a') as fid:
            for i in range(data.shape[1]):
                fid.write(data_format.format(time[i], *data[:, i]))
        self.write_count += 1


class HdfFile(OutputStream):
    """
    Create a single file with each stream as a separate data set
    """
    pass
