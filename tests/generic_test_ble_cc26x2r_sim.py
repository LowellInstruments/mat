import pytest


# todo > we can do an interface with this methods,
# todo > make this class implement that interface
# todo > so the classes which inherit from this class
# todo > are controlled


class GenericTestBleCC26X2:

    # purposely set to none, see below
    lc: None

    @pytest.mark.asyncio
    async def test_connect(self):
        # check lc is set by inheriting classes
        assert self.lc
        mac_sim = '11:22:33:44:55:66'
        assert await self.lc.connect(mac_sim) == 0
        mac_real = '60:77:71:22:c8:af'
        assert await self.lc.connect(mac_real) == 1
        # helps with rest of tests
        await self.lc.cmd_stp()

    @pytest.mark.asyncio
    async def test_cmd_sts(self):
        rv = await self.lc.cmd_sts()
        assert rv and rv[0] == 0

    @pytest.mark.asyncio
    async def test_cmd_frm(self):
        assert await self.lc.cmd_stp() == 0
        assert await self.lc.cmd_frm() == 0
        assert self.lc.files == {}

    @pytest.mark.asyncio
    async def test_cmd_cfg(self):
        await self.lc.cmd_stp()
        await self.lc.cmd_frm()
        assert 'MAT.cfg' not in self.lc.files
        assert await self.lc.cmd_cfg({}) == 0
        assert 'MAT.cfg' in self.lc.files

    @pytest.mark.asyncio
    async def test_cmd_dwg(self):
        await self.lc.cmd_stp()
        await self.lc.cmd_frm()
        await self.lc.cmd_cfg({})
        assert await self.lc.cmd_dwg('MAT.cfg') == 0
        assert await self.lc.cmd_dwg('made_up_filename.lid') == 1

    @pytest.mark.asyncio
    async def test_cmd_del(self):
        await self.lc.cmd_stp()
        s = 'mts_file'
        await self.lc.cmd_frm()
        assert s not in self.lc.files
        await self.lc.cmd_mts()
        assert s in self.lc.files
        await self.lc.cmd_del(s)
        assert s not in self.lc.files

    @pytest.mark.asyncio
    async def test_cmd_gtm(self):
        rv = await self.lc.cmd_gtm()
        assert rv and rv[0] == 0

    @pytest.mark.asyncio
    async def test_cmd_stm(self):
        await self.lc.cmd_stp()
        assert await self.lc.cmd_stm() == 0

    @pytest.mark.asyncio
    async def test_cmd_stp(self):
        assert await self.lc.cmd_stp() == 0

    @pytest.mark.asyncio
    async def test_cmd_sws(self):
        i = ('+1.111111', '-2.222222', None, None)
        assert await self.lc.cmd_sws(i) == 0

    @pytest.mark.asyncio
    async def test_cmd_rws(self):
        await self.lc.cmd_stp()
        i = ('+1.111111', '-2.222222', None, None)
        assert await self.lc.cmd_rws(i) == 0

    @pytest.mark.asyncio
    async def test_cmd_mts(self):
        await self.lc.cmd_stp()
        assert await self.lc.cmd_mts() == 0

    # DIR at the end so considers MTS
    @pytest.mark.asyncio
    async def test_cmd_dir(self):
        await self.lc.cmd_stp()
        await self.lc.cmd_frm()
        rv = await self.lc.cmd_dir()
        assert rv and rv == (0, {})
        await self.lc.cmd_mts()
        rv = await self.lc.cmd_dir()
        assert rv and len(rv[1]) == 1

    @pytest.mark.asyncio
    async def test_cmd_run(self):
        await self.lc.cmd_stp()
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
        await self.lc.cmd_stp()
        rv = await self.lc.cmd_wli('SN1234567')
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_utm(self):
        rv = await self.lc.cmd_utm()
        assert rv and rv[1] == '3 days'

    @pytest.mark.asyncio
    async def test_cmd_gdo(self):
        rv = await self.lc.cmd_gdo()
        assert rv and rv[0] != '0000'

    @pytest.mark.asyncio
    async def test_cmd_wat(self):
        rv = await self.lc.cmd_wat()
        assert rv[0] == 0 and 0 < rv[1] <= 3000

    @pytest.mark.asyncio
    async def test_cmd_wak(self):
        rv = await self.lc.cmd_wak('on')
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_rli(self):
        rv = await self.lc.cmd_rli()
        assert rv == 0

    @pytest.mark.asyncio
    async def test_cmd_dwl(self):
        await self.lc.cmd_stp()
        await self.lc.cmd_frm()
        await self.lc.cmd_mts()
        await self.lc.cmd_dwg('mts_file')
        rv = await self.lc.cmd_dwl(20480)
        assert rv == (0, b'my_data')

    @pytest.mark.asyncio
    async def test_cmd_crc(self):
        await self.lc.cmd_stp()
        await self.lc.cmd_frm()
        await self.lc.cmd_cfg({})
        rv = await self.lc.cmd_crc('kljfada.lid')
        assert rv and rv[0] == 1
        rv = await self.lc.cmd_crc('MAT.cfg')
        assert rv and rv[0] == 0

    @pytest.mark.asyncio
    async def test_disconnect(self):
        await self.lc.disconnect()
        assert self.lc.mac == ''
