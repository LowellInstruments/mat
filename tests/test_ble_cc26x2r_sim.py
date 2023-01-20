import pytest
from mat.ble.bleak.cc26x2r_sim import BleCC26X2Sim
from tests.generic_test_ble_cc26x2r import GenericTestBleCC26X2


class TestCC26X2Sim(GenericTestBleCC26X2):

    lc = BleCC26X2Sim()

    @pytest.mark.asyncio
    async def test_connect(self):
        mac_sim = '11:22:33:44:55:66'
        assert await self.lc.connect(mac_sim) == 0
        mac_real = '60:77:71:22:c8:af'
        assert await self.lc.connect(mac_real) == 1
