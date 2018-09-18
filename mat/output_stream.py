import numpy as np
from os import path, remove


def output_stream_factory(output_type, file_name, destination):
    output_types = {'csv': CsvStream}
    class_ = output_types.get(output_type)
    return class_(file_name, destination)


class OutputStream:
    def __init__(self, file_name, destination):
        self.file_name = file_name
        self.streams = {}
        self.destination = destination  # output directory for file output

    def add_stream(self, data_product):
        pass

    def set_header_string(self, stream, header_format):
        self.streams[stream].header_format = header_format

    def set_data_format(self, stream, data_format):
        self.streams[stream].data_format = data_format

    def set_time_format(self, stream, time_format):
        self.streams[stream].time_format = time_format

    def write(self, stream, data):
        self.streams[stream].write(data)


class CsvStream(OutputStream):
    """
    Create a different csv file for each stream
    """
    def add_stream(self, data_product):
        file_prefix = path.basename(self.file_name).split('.')[0]
        output_file_name = file_prefix + '_' + data_product + '.csv'
        output_path = path.join(self.destination, output_file_name)
        self.streams[data_product] = CsvFile(output_path)


class HdfFile(OutputStream):
    """
    Create a single file with each stream as a separate data set
    """
    pass


class CsvFile:
    EXTENSION = '.csv'

    def __init__(self, output_path):
        self.output_path = output_path
        self.header_str = ''
        self.data_format = ''
        self.time_format = 'iso8601'
        self.delete_output_file(output_path)

    def delete_output_file(self, output_path):
        try:
            remove(output_path)
        except FileNotFoundError:
            pass

    def write(self, data):
        data_format = self.data_format + '\r\n'
        with open(self.output_path, 'a') as fid:
            for i in range(np.shape(data)[1]):
                fid.write(data_format.format(*data[:, i]))
