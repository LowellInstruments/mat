# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

from mat import hoststorage
from mat import header
import numpy as np
import datetime
from abc import ABC, abstractmethod
from math import floor
from converter.data_file_registry import DataFileRegistry


class SensorDataFile(ABC):
    @classmethod
    def register(cls):
        DataFileRegistry.register(cls)

    @classmethod
    def create(cls, file_path):
        try:
            extension = file_path[-4:]
            return DataFileRegistry.registry[extension]()
        except KeyError:
            raise Exception('Invalid Filename')

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self._n_pages = None
        self._sensors = None

    def validate(self):
        # Figure out if this file is reasonable or raise an error
        return self

    def n_pages(self):
        if self._n_pages is None:
            self._n_pages = self.calc_n_pages()
        return self._n_pages

    def sensors(self):
        if self._sensors is None:
            self._sensors = self.create_sensors()
        return self._sensors

    def calc_n_pages(self):
        return 0

    def create_sensors(self):
        return []

    def load_page(self, i):
        return ""
