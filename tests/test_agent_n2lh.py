import time

from pynng import Pair0

from mat.agent_n2lh import PORT_N2LH, AgentN2LH, calc_n2lh_cmd_ans_timeout_secs, ClientN2LH
from mat.agent_utils import AG_N2LH_CMD_BYE, AG_BLE_CMD_QUERY, AG_BLE_CMD_STATUS, AG_BLE_CMD_LS_LID, \
    AG_BLE_CMD_GET_TIME, AG_N2LH_PATH_BLE
from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import FAKE_MAC_CC26X2, FAKE_MAC_RN4020, calc_ble_cmd_ans_timeout


url_lh = 'tcp4://localhost:{}'.format(PORT_N2LH)
url_lh_ext = 'tcp4://localhost:{}'.format(PORT_N2LH + 1)
# mac = '60:77:71:22:c8:18'
# mac = '60:77:71:22:c8:08'
# mac = FAKE_MAC_RN4020
mac = FAKE_MAC_CC26X2


class TestAgentN2LH:
    def test_n2lh_ble_commands(self):
        """ test won't finish because BLE thread but, meh """
        ag = AgentN2LH(url_lh, threaded=1)
        ag.start()
        list_of_cmd = [AG_BLE_CMD_QUERY,
                       AG_BLE_CMD_STATUS,
                       AG_BLE_CMD_GET_TIME,
                       AG_BLE_CMD_LS_LID,
                       AG_BLE_CMD_QUERY]

        for c in list_of_cmd:
            cmd = '{} {}'.format(c, mac)
            ClientN2LH(cmd, url_lh, None)


    def test_n2lh_ble_cmd_ans_timeout(self):
        t = calc_n2lh_cmd_ans_timeout_secs(AG_BLE_CMD_STATUS)
        assert t == calc_ble_cmd_ans_timeout(STATUS_CMD) * 1.1

    def test_n2lh_ble_get_file(self):
        if mac in [FAKE_MAC_CC26X2, FAKE_MAC_RN4020]:
            assert True
            return
        file, size = 'this_file.lid', 1234
        cmd = 'get_file {} . {} {}'.format(file, size, mac)
        ClientN2LH(cmd, url_lh, None)

        # an AgentN2LH_BLE will send the file now, so download it
        # todo: test this with real logger
        sk = Pair0(send_timeout=1000)
        self.sk.listen(url_lh_ext)
        self.sk.recv_timeout = 1000
        b = sk.recv()
        rx_file = '_n2lh_{}'.format(file)
        with open(rx_file, 'wb') as f:
            f.write(b)
            f.truncate(int(size))
        sk.close()
        assert len(b) == int(size)
