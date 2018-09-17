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


def assert_compare_expected_file(file_name):
    new_path = reference_file(file_name)
    expected_path = reference_file(file_name + ".expect")
    with open(new_path) as new_file, open(expected_path) as expected_file:
        new_lines = [line.strip() for line in new_file.readlines()]
        expected_lines = [line.strip() for line in expected_file.readlines()]
    os.remove(new_path)
    assert new_lines == expected_lines
