# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


from setuptools import setup, find_packages
import os


# grab packages from requirements files
with open('requirements.txt') as f:
    rr = f.readlines()


# obtain package version from local file
v = {}
with open("mat/version.py") as f:
    exec(f.read(), v)


# option 1) export MY_IGNORE_REQUIREMENTS_TXT=1 && pip install . -v
# option 2) or, just 'pip install' will install requirements_311.txt contents
if os.getenv('MY_IGNORE_REQUIREMENTS_TXT') == '1':
    rr = []


setup(name='lowell-mat',
      version=v['__version__'],
      description='Shared package for Lowell Instruments software',
      url='https://github.com/LowellInstruments/lowell-mat',
      author='Lowell Instruments',
      author_email='software@lowellinstruments.com',
      packages=find_packages(),
      install_requires=rr,
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