from os import path
from .time_converter import create_time_converter
from pathlib import Path
import h5py
import numpy as np


def output_stream_factory(file_path, parameters):
    output_types = {'csv': CsvStream, 'hdf5': HDF5Stream}
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
        self.overwrite = True

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

    def set_overwrite(self, state):
        self.overwrite = state
        for name in self.streams:
            self.streams[name].overwrite = state


class CsvStream(OutputStream):
    def add_stream(self, data_product):
        self.streams[data_product] = CsvFile(
            self.file_path, data_product, self.parameters
        )


class HDF5Stream(OutputStream):
    hdf_file = None

    def __init__(self, file_path, parameters):
        super().__init__(file_path, parameters)
        self.time_converter = create_time_converter('iso8601')
        if HDF5Stream.hdf_file:
            return
        path = Path(file_path)
        hdf_path = (path.parent / path.stem).with_suffix('.hdf5')
        if hdf_path.exists() and not self.overwrite:
            raise FileExistsError(str(path.name))
        HDF5Stream.hdf_file = h5py.File(hdf_path, 'w')

    def file(self):
        return HDF5Stream.hdf_file

    def add_stream(self, data_product):
        self.streams[data_product] = self.file().create_group(data_product)

    def set_column_header(self, stream, column_header):
        self.streams[stream].create_dataset(
            'Time', (0, ),
            maxshape=(None, ),
            dtype='S23',
            compression='gzip',
            shuffle=True
        )
        self.streams[stream]['Time'].attrs['Columns'] = 'ISO 8601 Time'

        channels = column_header.split(',')
        self.streams[stream].create_dataset(
            'Data',
            (0, len(channels)),
            maxshape=(None, len(channels)),
            compression='gzip',
            shuffle=True
        )
        self.streams[stream]['Data'].attrs['Columns'] = column_header

    def write(self, stream, data, time):
        ds_data = self.streams[stream]['Data']
        ds_time = self.streams[stream]['Time']

        ds_shape = ds_data.shape
        new_length = ds_shape[0] + data.shape[1]

        ds_data.resize((new_length, ds_shape[1]))
        ds_time.resize((new_length, ))
        ds_data[ds_shape[0]:, :] = data.T
        ds_time[ds_shape[0]:] = np.string_(self.time_converter.convert(time))


class CsvFile:
    def __init__(self, file_path, stream_name, parameters):
        self.file_path = file_path
        self.stream_name = stream_name
        self.parameters = parameters
        self.column_header = ''
        self.data_format = ''
        self.split = parameters['split'] or 100000
        self.write_count = 0
        self.output_file_name = ''
        self.output_path = ''
        self.overwrite = True

    def next_file_path(self):
        dir_name = path.dirname(self.file_path)
        destination = self.parameters['output_directory'] or dir_name
        if self.parameters['file_name']:
            file_prefix = self.parameters['file_name']
        else:
            file_prefix = path.basename(self.file_path).split('.')[0]
        file_num = self.write_count // self.split
        file_num_str = '_{}'.format(file_num) if self.split != 100000 else ''
        self.output_file_name = '{}_{}{}.csv'.format(file_prefix,
                                                     self.stream_name,
                                                     file_num_str)
        self.output_path = path.join(destination, self.output_file_name)

    def write(self, data, time):
        if self.write_count % self.split == 0:
            self.next_file_path()
            if path.exists(self.output_path) and not self.overwrite:
                raise FileExistsError(self.output_file_name)
            self._write_header()

        data_format = '{},' + self.data_format + '\n'
        with open(self.output_path, 'a') as fid:
            for i in range(data.shape[1]):
                fid.write(data_format.format(time[i], *data[:, i]))
        self.write_count += 1

    def _write_header(self):
        with open(self.output_path, 'w') as fid:
            fid.write(self.column_header + '\n')
