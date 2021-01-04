import queue
import threading

from mat.agent_n2lh_ble import AgentN2LH_BLE
from mat.agent_utils import *
import time
import json
from mat.logger_controller_ble_dummy import FAKE_MAC_CC26X2, FAKE_MAC_RN4020

# mac_lab = '60:77:71:22:c8:08'
# mac_house = '60:77:71:22:c8:18'
mac_testing_cc26x2 = FAKE_MAC_CC26X2
# mac_testing_rn4020 = FAKE_MAC_RN4020
mac = mac_testing_cc26x2


def _p(s):
    print(s)


class TestAgentN2LH_BLE:
    """ tests AgentN2LH_BLE directly, omitting AgentN2LH layer """
    q_to_ble = queue.Queue()
    q_from_ble = queue.Queue()

    def _q(self, _in):
        self.q_to_ble.put(_in)
        _out = self.q_from_ble.get()
        return _out

    def _end_ag_ble_th(self):
        s = '{} {}'.format(AG_BLE_END_THREAD, mac)
        self._q(s)

    def test_disconnect_was_not_connected(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        # skipping connect() on purpose
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        rv = self._q(s)
        assert AG_BLE_ANS_DISC_ALREADY in rv[1]
        self._end_ag_ble_th()

    def test_connect_disconnect(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q( s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        rv = self._q(s)
        assert rv[0] == 0
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        rv = self._q(s)
        assert rv[0] == 0
        assert AG_BLE_ANS_DISC_OK in rv[1]
        self._end_ag_ble_th()

    def test_connect_already(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        self._q(s)
        s = '{} {}'.format(AG_BLE_CMD_CONNECT, mac)
        rv = self._q(s)
        assert AG_BLE_ANS_CONN_ALREADY in rv[1]
        self._end_ag_ble_th()

    def test_get_time_thrice_few_time_same_connection(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        # the first command implicitly connects so takes > 1 second
        now = time.perf_counter()
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = self._q(s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        assert el > 1
        _p('1st {} took {}'.format(AG_BLE_CMD_GET_TIME, el))
        # the next 2 are much faster
        now = time.perf_counter()
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = self._q(s)
        assert rv[0] == 0
        s = '{} {}'.format(AG_BLE_CMD_GET_TIME, mac)
        rv = self._q(s)
        assert rv[0] == 0
        el = time.perf_counter() - now
        _p('2nd & 3rd {} took {}'.format(AG_BLE_CMD_GET_TIME, el))
        assert el < .5
        self._end_ag_ble_th()

    def test_set_time(self):
        # sync_time is different than STM but, meh
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        # although in test the 'd' time string is ignored
        d = '2019/03/01 16:47:51'
        s = '{} {} {}'.format(AG_BLE_CMD_SET_TIME, d, mac)
        rv = self._q(s)
        assert rv[0] == 0
        self._end_ag_ble_th()

    def test_get_fake_file(self):
        # too difficult to test on dummies
        if mac in [FAKE_MAC_RN4020, FAKE_MAC_CC26X2]:
            assert True
            return

        # this long test may take a couple minutes
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        file = 'a.lid'
        size = 1234
        fol = '.'
        s = '{} {} {} {} {}'
        s = s.format(AG_BLE_CMD_GET_FILE, file, fol, size, mac)
        rv = self._q(s)
        assert rv[0] == 0
        self._end_ag_ble_th()

    def test_ls_lid(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        s = '{} {}'.format(AG_BLE_CMD_LS_LID, mac)
        rv = self._q(s)
        _p(rv)
        assert rv[0] == 0
        self._end_ag_ble_th()

    def test_ls_not_lid(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        s = '{} {}'.format(AG_BLE_CMD_LS_NOT_LID, mac)
        rv = self._q(s)
        _p(rv)
        assert rv[0] == 0
        self._end_ag_ble_th()

    def test_stop(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_STOP, mac)
        rv = self._q(s)
        assert rv[0] == 0
        self._end_ag_ble_th()

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
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_STOP, mac)
        self._q(s)
        # _cfg: dict -> string
        _cfg = json.dumps(_cfg)
        s = '{} ${}$ {}'.format(AG_BLE_CMD_CONFIG, _cfg, mac)
        rv = self._q(s)
        assert rv[0] == 0
        self._end_ag_ble_th()

    def test_mts_cmd(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        s = '{} {}'.format(AG_BLE_CMD_MTS, mac)
        rv = self._q(s)
        _p(rv)
        assert rv[0] == 0
        self._end_ag_ble_th()

    def test_any_cmd(self):
        ag_ble = AgentN2LH_BLE(self.q_to_ble, self.q_from_ble)
        th_ag_ble = threading.Thread(target=ag_ble.loop_ag_ble)
        th_ag_ble.start()
        s = '{} {}'.format(AG_BLE_CMD_DISCONNECT, mac)
        self._q(s)
        s = '{} {}'.format(AG_BLE_CMD_LS_LID, mac)
        rv = self._q(s)
        _p(rv)
        s = '{} {}'.format(AG_BLE_CMD_LS_NOT_LID, mac)
        rv = self._q(s)
        _p(rv)
        assert rv[0] == 0
        self._end_ag_ble_th()
