# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


from unittest import TestCase
from mat.data_converter import ConversionParameters


class TestConversionParameters(TestCase):
    def test_bad_kwargs(self):
        with self.assertRaises(ValueError):
            ConversionParameters("path", bad_kwarg=True)
