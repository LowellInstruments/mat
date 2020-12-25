from mat.agent_n2lh_ble import AgentN2LH_BLE
from mat.agent_utils import *
import time
import json
from mat.logger_controller_ble import FAKE_MAC_CC26X2, FAKE_MAC_RN4020

# mac_lab = '60:77:71:22:c8:08'
# mac_house = '60:77:71:22:c8:18'
mac_testing_cc26x2 = FAKE_MAC_CC26X2
# mac_testing_rn4020 = FAKE_MAC_RN4020
mac = mac_testing_cc26x2


def _p(s):
    print(s)


class TestAgentN2LH_BLE:
    """ tests AgentN2LH_BLE directly, omitting AgentN2LH layer """

    def test_disconnect_was_not_connected(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        # skip connect() on purpose
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        rv = _q(ag, s)
        assert AG_BLE_ANS_DISC_ALREADY in rv[1]

    def test_connect_disconnect(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        assert AG_BLE_ANS_DISC_OK in rv[1]

    def test_connect_already(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        rv = _q(ag, s)
        assert AG_BLE_ANS_CONN_ALREADY in rv[1]

    def test_get_time_thrice_few_time_same_connection(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        # the first command implicitly connects so takes > 1 second
        now = time.perf_counter()
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        assert el > 1
        _p('1st {} took {}'.format(AG_BLE_CMD_GET_TIME, el))
        # the next 2 are much faster
        now = time.perf_counter()
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        _p('2nd & 3rd {} took {}'.format(AG_BLE_CMD_GET_TIME, el))
        assert el < .5

    def test_set_time(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_SET_TIME, mac)
        rv = _q(ag, s)
        assert rv[0] == 0

    def test_get_fake_file(self):
        # too difficult to test on dummies
        if mac in [FAKE_MAC_RN4020, FAKE_MAC_CC26X2]:
            assert True
            return

        # this long test may take a couple minutes
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        file = 'a.lid'
        size = 1234
        fol = '.'
        s = '{} {} {} {} {}'
        s = s.format(AG_BLE_CMD_GET_FILE, file, fol, size, mac)
        rv = _q(ag, s)
        assert rv[0] == 0

    def test_ls_lid(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_LS_LID, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0

    def test_ls_not_lid(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_LS_NOT_LID, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0

    def test_stop(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_STOP, mac)
        rv = _q(ag, s)
        assert rv[0] == 0

    def test_config_cmd(self):
        _cfg = {
            "DFN": "low",
            "TMP": 0, "PRS": 0,
            "DOS": 1, "DOP": 1, "DOT": 1,
            "TRI": 10, "ORI": 10, "DRI": 900,
            "PRR": 8,
            "PRN": 4,
            "STM": "2012-11-12 12:14:00",
            "ETM": "2030-11-12 12:14:20",
            "LED": 1
        }
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_STOP, mac)
        _q(ag, s)
        # _cfg: dict -> string
        _cfg = json.dumps(_cfg)
        s = '{} ${}$ {}'.format(AG_BLE_CMD_CONFIG, _cfg, mac)
        rv = _q(ag, s)
        assert rv[0] == 0

    def test_mts_cmd(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_MTS, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0

    def test_any_cmd(self):
        ag = AgentN2LH_BLE(threaded=1)
        ag.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        _q(ag, s)
        s = '{} {}'.format(AG_BLE_CMD_LS_LID, mac)
        rv = _q(ag, s)
        _p(rv)
        s = '{} {}'.format(AG_BLE_CMD_LS_NOT_LID, mac)
        rv = _q(ag, s)
        _p(rv)
        assert rv[0] == 0


def _q(_ag, _in):
    _ag.q_in.put(_in)
    _out = _ag.q_out.get()
    return _out
