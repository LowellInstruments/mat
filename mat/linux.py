import os
import pathlib
from platform import machine


def linux_is_docker():
    return pathlib.Path('/.dockerenv').is_file()


def linux_is_x64():
    return machine() == 'x86_64'


def linux_is_docker_on_x64():
    return linux_is_docker() and linux_is_x64()


def linux_is_rpi():
    # this better than checking architecture
    if os.uname().nodename in ('raspberrypi', 'rpi'):
        return True
    return False


def linux_is_docker_on_rpi():
    return linux_is_docker() and linux_is_rpi()
