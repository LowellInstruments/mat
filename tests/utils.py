import os
from mat.calibration_factories import make_from_calibration_file


def reference_file(file_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "files",
        file_name)


def calibration_from_file(file_name):
    file = reference_file(file_name)
    return make_from_calibration_file(file)
