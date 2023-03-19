from mat.version import get_mat_lib_version
from mat.version import __version__ as _V_


class TestVersion:
    def test_version(self):
        assert get_mat_lib_version() == _V_
