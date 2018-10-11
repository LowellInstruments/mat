from mat.lid_data_file import LidDataFile
from mat.lis_data_file import LisDataFile


DATA_FILE_TYPES = {'.lid': LidDataFile,
                   '.lis': LisDataFile}


def load_data_file(file_path):
    extension = file_path[-4:]
    try:
        klass = DATA_FILE_TYPES.get(extension)
        return klass(file_path)
    except TypeError:
        raise ValueError('Invalid Filename or extension')
