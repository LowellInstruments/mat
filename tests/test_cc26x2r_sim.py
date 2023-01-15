import asyncio
import pytest
from mat.ble.bleak.cc26x2r_sim import BleCC26X2Sim


lc: BleCC26X2Sim


class TestCC26X2rSim:

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(self):
        global lc
        lc = BleCC26X2Sim()
        yield

    @pytest.mark.asyncio
    async def test_cmd_sts(self):
        rv = await lc.cmd_sts()
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_dwg(self):
        rv = await lc.cmd_dwg('MAT.cfg')
        assert rv == 0
        rv = await lc.cmd_dwg('made_up_filename.lid')
        assert rv == 1

    @pytest.mark.asyncio
    async def test_cmd_del(self):
        rv = await lc.cmd_del('MAT.cfg')
        assert rv == 0
        rv = await lc.cmd_del('made_up_filename.lid')
        assert rv == 1

    @pytest.mark.asyncio
    async def test_cmd_stm(self):
        rv = await lc.cmd_stm()
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_stp(self):
        rv = await lc.cmd_stp()
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_frm(self):
        rv = await lc.cmd_frm()
        assert rv == 0

