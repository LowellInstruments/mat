from mat.lid_data_file import LidDataFile


DATA_FILE_TYPES = {'.lid': LidDataFile}


def load_data_file(file_path):
    extension = file_path[-4:]
    try:
        klass = DATA_FILE_TYPES.get(extension)
        return klass(file_path)
    except TypeError:
        raise ValueError('Invalid Filename or extension')
