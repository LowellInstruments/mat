from os import path, remove
from .time_converter import create_time_converter


def output_stream_factory(output_type, file_name, destination, time_format):
    output_types = {'csv': CsvStream}
    stream_class = output_types.get(output_type)
    if stream_class is None:
        raise ValueError('Unknown output type' + output_type)
    return stream_class(file_name, destination, time_format)


class OutputStream:
    def __init__(self, file_name, destination, time_format):
        self.file_name = file_name
        self.streams = {}
        self.destination = destination  # output directory for file output
        self.time_converter = create_time_converter(time_format)

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

    def write_header(self, stream):
        self.streams[stream].write_header()


class CsvStream(OutputStream):
    """
    Create a different csv file for each stream
    """
    def add_stream(self, data_product):
        file_prefix = path.basename(self.file_name).split('.')[0]
        output_file_name = file_prefix + '_' + data_product + '.csv'
        output_path = path.join(self.destination, output_file_name)
        self.streams[data_product] = CsvFile(output_path)


class CsvFile:
    EXTENSION = '.csv'

    def __init__(self, output_path):
        self.output_path = output_path
        self.column_header = ''
        self.data_format = ''
        self.delete_output_file(output_path)

    def delete_output_file(self, output_path):
        try:
            remove(output_path)
        except FileNotFoundError:
            pass

    def write_header(self):
        with open(self.output_path, 'a') as fid:
            fid.write(self.column_header + '\n')

    def write(self, data, time):
        data_format = '{},' + self.data_format + '\n'
        with open(self.output_path, 'a') as fid:
            for i in range(data.shape[1]):
                fid.write(data_format.format(time[i], *data[:, i]))


class HdfFile(OutputStream):
    """
    Create a single file with each stream as a separate data set
    """
    pass
