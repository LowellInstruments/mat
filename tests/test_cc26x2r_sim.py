import asyncio
import pytest
from mat.ble.bleak.cc26x2r_sim import BleCC26X2Sim


lc: BleCC26X2Sim


class TestCC26X2rSim:

    @pytest.fixture(autouse=True)
    def run_before_and_after_tests(self):
        global lc
        # todo > I think this is wrong because regenerates files
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

    @pytest.mark.asyncio
    async def test_cmd_sws(self):
        i = ('+1.111111', '-2.222222', None, None)
        rv = await lc.cmd_sws(i)
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_rws(self):
        i = ('+1.111111', '-2.222222', None, None)
        rv = await lc.cmd_rws(i)
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_gtm(self):
        rv = await lc.cmd_gtm()
        assert rv and rv[0] == 0

    @pytest.mark.asyncio
    async def test_cmd_mts(self):
        rv = await lc.cmd_mts()
        assert rv == 0

    # DIR at the end so considers MTS
    @pytest.mark.asyncio
    async def test_cmd_dir(self):
        rv = await lc.cmd_dir()
        print('\nDIR {}'.format(rv))
        assert rv and rv[0] == 0
