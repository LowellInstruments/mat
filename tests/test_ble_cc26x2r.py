import pytest
from mat.ble.bleak.cc26x2r import BleCC26X2
from tests.test_ble_cc26x2r_sim import TestCC26X2RSim


class TestCC26X2R(TestCC26X2RSim):

    # -----------------------------------
    # the BLE logger type we are testing
    # -----------------------------------
    lc = BleCC26X2()

