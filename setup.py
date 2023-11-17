# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


from setuptools import setup, find_packages
import os


# obtain package version from local file
v = {}
with open("mat/version.py") as f:
    exec(f.read(), v)


setup(name='mat',
      version=v['__version__'],
      description='Shared package for Lowell Instruments software',
      url='https://github.com/LowellInstruments/mat',
      author='Lowell Instruments',
      author_email='software@lowellinstruments.com',
      packages=find_packages(),
      install_requires=[
          'h5py',
          'numpy',
          'pyserial',
          'bleak',
          'humanize',
          'boto3',
          'awscli',
          'tzlocal',
          'pandas',
          'python-dateutil'
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
