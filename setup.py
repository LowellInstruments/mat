# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved
from setuptools import setup, find_packages
import platform
from mat.utils import linux_is_rpi


# version management
v = {}
with open("mat/version.py") as fp:
    exec(fp.read(), v)


np = 'numpy'
h5py = 'h5py'
if platform.system() == 'Linux' and linux_is_rpi():
    np = 'numpy>=1.16.5'
    h5py = 'h5py>=2.10.0'


setup(name='lowell-mat',
      version=v['__version__'],
      description='Shared package for Lowell Instruments software',
      url='https://github.com/LowellInstruments/lowell-mat',
      author='Lowell Instruments',
      author_email='software@lowellinstruments.com',
      packages=find_packages(),
      install_requires=[
          'h5py',
          np,
          'pyserial>=3.5',
          'pandas',
          'boto3'
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
