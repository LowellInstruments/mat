import pathlib

from mat.data_converter import DataConverter, default_parameters


def cnv(path):
    path = str(path)
    try:
        parameters = default_parameters()
        converter = DataConverter(path, parameters)
        converter.convert()
        print('{} converted OK'.format(path))
    except Exception as ex:
        print('ERROR converting {}\n\t{}'.format(path, ex))


if __name__ == '__main__':
    name = 'dummy_425.lid'
    s = pathlib.Path.home() / 'Downloads' / name
    cnv(s)
