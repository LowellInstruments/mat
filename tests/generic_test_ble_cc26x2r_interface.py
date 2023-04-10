import abc


class GenericTestBleCC26X2Interface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def test_connect(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_sts(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_frm(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_cfg(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_dwg(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_del(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_gtm(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_stm(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_stp(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_sws(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_rws(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_mts(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_dir(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_run(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_gfv(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_bat(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_wli(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_utm(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_gdo(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_wat(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_wak(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_rli(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_dwl(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_cmd_crc(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def test_disconnect(self):
        raise NotImplementedError
