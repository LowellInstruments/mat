# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved
from setuptools import setup, find_packages
import subprocess as sp

# -------------------
# version management
# -------------------

v = {}
with open("mat/version.py") as fp:
    exec(fp.read(), v)


# todo > should we put ALL reqs in lowell-mat-dependant apps and zero in here?

setup(name='lowell-mat',
      version=v['__version__'],
      description='Shared package for Lowell Instruments software',
      url='https://github.com/LowellInstruments/lowell-mat',
      author='Lowell Instruments',
      author_email='software@lowellinstruments.com',
      packages=find_packages(),
      install_requires=[
          'h5py~=3.7.0',
          'numpy~=1.21.4',
          'pyserial~=3.5',
          'pandas~=1.3.5',
          'humanize~=4.3.0',
          'bleak~=0.17.0',
          'awscli~=1.27.4',
          'boto3~=1.26.4',
          'tzlocal~=2.1'

      ],
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
