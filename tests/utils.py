import os


def reference_file(file_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "files",
        file_name)
