import os
import pickle


def get_userdata(filename):
    if os.name == 'nt':
        appdata_path = os.getenv('APPDATA')
        path = os.path.join(appdata_path, 'Lowell Instruments\\' + filename)
    elif os.name == 'posix':
        appdata_path = os.environ['HOME']
        path = os.path.join(appdata_path, '.config/.Lowell/' + filename)
    else:
        raise SystemError('Unknown system type')
    if os.path.isfile(path):
        with open(path, 'rb') as h:
            return pickle.load(h)
    else:
        return {}


def set_userdata(filename, field, data):
    if os.name == 'nt':
        appdata_path = os.getenv('APPDATA')
        path = appdata_path + '\\Lowell Instruments'
    elif os.name == 'posix':
        appdata_path = os.getenv('HOME')
        path = os.path.join(appdata_path, '.config/.Lowell')
    else:
        raise SystemError('Unknown system type')
    if not os.path.exists(path):
        os.makedirs(path)
    userdata = get_userdata(filename)
    userdata[field] = data

    with open(os.path.join(path, filename), 'wb') as h:
        pickle.dump(userdata, h)