# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

from mat import hoststorage
from mat import header
import numpy as np
import datetime
from abc import ABC, abstractmethod
from math import floor
from mat.data_file_registry import DataFileRegistry


class SensorDataFile(ABC):
    @classmethod
    def register(cls):
        DataFileRegistry.register(cls)

    @classmethod
    def create(cls, file_path):
        try:
            extension = file_path[-4:]
            return DataFileRegistry.registry[extension](file_path)
        except KeyError:
            raise ValueError('Invalid Filename')

    def __init__(self, file_path):
        self._file_path = file_path
        self._file = None
        self._n_pages = None
        self._sensors = None

    def __del__(self):
        if self._file:
            self.close()

    def close(self):
        if self._file:
            self._file.close()
        self._file = None

    def validate(self):
        # Figure out if this file is reasonable or raise an error
        pass

    def file(self):
        if self._file is None:
            self._file = open(self._file_path, "rb")
        return self._file

    def n_pages(self):
        if self._n_pages is None:
            self._n_pages = self._calc_n_pages()
        return self._n_pages

    def sensors(self):
        if self._sensors is None:
            self._sensors = self._create_sensors()
        return self._sensors

    def _calc_n_pages(self):
        return 1

    def _create_sensors(self):
        return []

    def load_page(self, i):
        return ""
