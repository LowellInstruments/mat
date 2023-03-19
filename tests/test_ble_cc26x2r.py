from mat.ble.bleak.cc26x2r import BleCC26X2
from tests.generic_test_ble_cc26x2r import GenericTestBleCC26X2


class TestCC26X2Sim(GenericTestBleCC26X2):
    lc = BleCC26X2()
