import asyncio
import pytest
from mat.ble.bleak.cc26x2r_sim import BleCC26X2Sim


class TestCC26X2rSim:

    lc = BleCC26X2Sim()

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(self):
        yield

    @pytest.mark.asyncio
    async def test_connect(self):
        mac_sim = '11:22:33:44:55:66'
        assert await self.lc.connect(mac_sim) == 0
        mac_real = '60:77:71:22:c8:af'
        assert await self.lc.connect(mac_real) == 1

#     @pytest.mark.asyncio
#     async def test_cmd_sts(self):
#         rv = await self.lc.cmd_sts()
#         assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_dwg(self):
        assert await self.lc.cmd_dwg('MAT.cfg') == 0
        assert await self.lc.cmd_dwg('made_up_filename.lid') == 1

    @pytest.mark.asyncio
    async def test_cmd_del(self):
        assert await self.lc.cmd_del('MAT.cfg') == 0
        assert await self.lc.cmd_del('made_up_filename.lid') == 1

    @pytest.mark.asyncio
    async def test_cmd_gtm(self):
        rv = await self.lc.cmd_gtm()
        assert rv and rv[0] == 0

    @pytest.mark.asyncio
    async def test_cmd_stm(self):
        assert await self.lc.cmd_stm() == 0

    @pytest.mark.asyncio
    async def test_cmd_stp(self):
        assert await self.lc.cmd_stp() == 0

    @pytest.mark.asyncio
    async def test_cmd_frm(self):
        assert await self.lc.cmd_stp() == 0

    @pytest.mark.asyncio
    async def test_cmd_sws(self):
        i = ('+1.111111', '-2.222222', None, None)
        assert await self.lc.cmd_sws(i) == 0

    @pytest.mark.asyncio
    async def test_cmd_rws(self):
        i = ('+1.111111', '-2.222222', None, None)
        assert await self.lc.cmd_rws(i) == 0

    @pytest.mark.asyncio
    async def test_cmd_mts(self):
        assert await self.lc.cmd_mts() == 0

    # DIR at the end so considers MTS
    @pytest.mark.asyncio
    async def test_cmd_dir(self):
        await self.lc.cmd_frm()
        rv = await self.lc.cmd_dir()
        assert rv and rv == (0, {})
        await self.lc.cmd_mts()
        rv = await self.lc.cmd_dir()
        assert rv and len(rv[1]) == 1

    @pytest.mark.asyncio
    async def test_cmd_cfg(self):
        await self.lc.cmd_frm()
        rv = await self.lc.cmd_dir()
        assert rv and rv == (0, {})
        test_cfg_dict = {}
        assert await self.lc.cmd_cfg(test_cfg_dict) == 0
        rv = await self.lc.cmd_dir()
        assert rv and len(rv[1]) == 1

    @pytest.mark.asyncio
    async def test_cmd_run(self):
        assert await self.lc.cmd_run() == 0

    @pytest.mark.asyncio
    async def test_cmd_gfv(self):
        rv = await self.lc.cmd_gfv()
        assert rv and len(rv[1]) == 6

    @pytest.mark.asyncio
    async def test_cmd_bat(self):
        rv = await self.lc.cmd_bat()
        assert rv and type(rv[1]) is int and rv[1] > 0

    @pytest.mark.asyncio
    async def test_cmd_wli(self):
        rv = await self.lc.cmd_wli('SN1234567')
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_utm(self):
        rv = await self.lc.cmd_utm()
        assert rv and rv[1] == '3 days'

    @pytest.mark.asyncio
    async def test_disconnect(self):
        await self.lc.disconnect()
        assert self.lc.mac == ''

