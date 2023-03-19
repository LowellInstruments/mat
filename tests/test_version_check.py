from mat.version_check import VersionChecker


class TestVersionCheck:
    def test_version_check(self):
        vc = VersionChecker()
        # this seems not clearly defined by Jeff
        vc.get_latest_version()

    def test_version_is_latest(self):
        vc = VersionChecker()
        assert vc.is_latest('9999')
