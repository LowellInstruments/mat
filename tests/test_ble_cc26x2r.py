import pytest
from mat.ble.bleak.cc26x2r import BleCC26X2
from tests.generic_test_ble_cc26x2r import GenericTestBleCC26X2
import platform


@pytest.mark.skipif(
    platform.node() != 'ARCHER',
    reason='only test BLE hardware on development laptop'
)
class TestBleCC26X2(GenericTestBleCC26X2):

    lc = BleCC26X2()
