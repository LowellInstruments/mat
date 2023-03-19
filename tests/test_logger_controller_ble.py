class TestLoggerControllerBle:
    def test_all_definitions(self):
        with open('../mat/logger_controller_ble.py') as f:
            ll = f.readlines()
            for i in ll:
                if '=' not in i:
                    continue
                assert '' not in i
