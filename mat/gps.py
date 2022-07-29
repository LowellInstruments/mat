import time
import datetime
import serial
import sys
from serial import SerialException


# hardcoded, since they are FIXED on SixFab hats
PORT_CTRL = '/dev/ttyUSB2'
PORT_DATA = '/dev/ttyUSB1'

