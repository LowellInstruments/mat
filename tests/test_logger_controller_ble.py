import os


class TestLoggerControllerBle:
    def test_all_definitions(self):
        # local tests
        path = '../mat/logger_controller_ble.py'
        if os.getenv('GITHUB_ACTIONS'):
            path = 'mat/logger_controller_ble.py'
        with open(path) as f:
            ll = f.readlines()
            for i in ll:
                if '=' not in i:
                    continue
                assert "''" not in i
