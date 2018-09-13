from mat.lid_data_file import LidDataFile
from mat.lis_data_file import LisDataFile


DATA_FILE_TYPES = {'.lid': LidDataFile,
                   '.lis': LisDataFile}


def create(file_path):
    extension = file_path[-4:]
    try:
        class_ = DATA_FILE_TYPES.get(extension)
        return class_(file_path)
    except TypeError:
        raise ValueError('Invalid Filename or extension')
