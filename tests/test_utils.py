from mat.utils import linux_is_rpi, linux_is_rpi4, linux_is_rpi3, is_valid_mac_address, linux_ls_by_ext


class TestUtils:
    def test_utils(self):
        # we will never test this on RPi, will we
        assert not linux_is_rpi()
        assert not linux_is_rpi4()
        assert not linux_is_rpi3()
        assert is_valid_mac_address('11:22:33:44:55:66')
        assert not is_valid_mac_address('hello')
        assert linux_ls_by_ext('.', '*')
