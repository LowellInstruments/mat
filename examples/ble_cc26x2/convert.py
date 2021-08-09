from mat.data_converter import DataConverter, default_parameters


def cnv(path):
    try:
        print('\t\tConverting --> {}'.format(path), end='')
        parameters = default_parameters()
        converter = DataConverter(path, parameters)
        converter.convert()
        print('  ok')
    except Exception as ex:
        print('  error')
        print(ex)


if __name__ == '__main__':
    cnv('li_data.lid')
