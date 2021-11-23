# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved
import platform
from setuptools import setup, find_packages

# installation uses "requirements.txt", but it removes the
# git+ format used in it because setup.py does not like it
rr = list(map(str.strip, open("requirements.txt").readlines()))
rr.remove('git+https://github.com/LowellInstruments/bluepy.git')


# add our bluepy, but only for Linux installations
if platform.system() == 'Linux':
    rr.append('bluepy @ https://github.com/LowellInstruments/bluepy/archive/refs/heads/master.zip')


# version management
v = {}
with open("mat/version.py") as fp:
    exec(fp.read(), v)


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
