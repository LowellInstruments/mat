# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved
import os
from setuptools import setup

requirements = [
    'numpy',
    'pyserial',
    'h5py==2.10.0'
]
if os.name == 'posix':
    requirements.extend([
        'bluepy@git+https://github.com/LowellInstruments/bluepy.git',
        'crc16==0.1.1'
    ])

setup(name='lowell-mat',
      version='1.2',
      description='Shared package for Lowell Instruments software',
      url='https://github.com/LowellInstruments/lowell-mat',
      author='Lowell Instruments',
      author_email='software@lowellinstruments.com',
      packages=['mat'],
      install_requires=requirements,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Environment :: MacOS X",
          "Environment :: Win32 (MS Windows)",
          "Environment :: X11 Applications",
          "Environment :: X11 Applications :: Qt",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
          "Natural Language :: English",
          "Operating System :: MacOS",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: Microsoft",
          "Operating System :: Microsoft :: Windows",
          "Operating System :: Microsoft :: Windows :: Windows 10",
          "Operating System :: Microsoft :: Windows :: Windows 7",
          "Operating System :: Microsoft :: Windows :: Windows 8",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.6",
      ])
