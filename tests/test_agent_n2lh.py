import threading

from mat.agent_n2lh import PORT_N2LH, AgentN2LH, ClientN2LH, \
    calc_n2lh_cmd_ans_timeout_ms
from mat.agent_utils import AG_BLE_CMD_QUERY, AG_BLE_CMD_STATUS, AG_BLE_CMD_LS_LID, \
    AG_BLE_CMD_GET_TIME, AG_BLE_END_THREAD, AG_N2LH_END_THREAD, AG_N2LH_PATH_BASE, AG_N2LH_PATH_BLE, AG_BLE_CMD_CRC
from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import calc_ble_cmd_ans_timeout, CRC_CMD
from mat.logger_controller_ble_dummy import FAKE_MAC_CC26X2


url_lh = 'tcp4://localhost:{}'.format(PORT_N2LH)
# mac = '60:77:71:22:c8:18'
# mac = '60:77:71:22:c8:08'
# mac = FAKE_MAC_RN4020
mac = FAKE_MAC_CC26X2


class TestAgentN2LH:
    """ tests AgentN2LH underlying agents """

    def test_n2lh_ble_commands(self):
        ag = AgentN2LH(url_lh)
        th_ag_ble = threading.Thread(target=ag.loop_n2lh)
        th_ag_ble.start()
        list_of_cmd = [AG_BLE_CMD_QUERY,
                       AG_BLE_CMD_STATUS,
                       AG_BLE_CMD_GET_TIME,
                       AG_BLE_CMD_LS_LID,
                       AG_BLE_CMD_QUERY]

        for c in list_of_cmd:
            t = calc_n2lh_cmd_ans_timeout_ms(c)
            cmd = '{} {}'.format(c, mac)
            ClientN2LH(cmd, url_lh).do(AG_N2LH_PATH_BLE, t)

        # make N2LH_BLE and N2LH_BASE threads end
        cmd = '{} {}'.format(AG_BLE_END_THREAD, mac)
        ClientN2LH(cmd, url_lh).do(AG_N2LH_PATH_BLE, 1000)
        cmd = '{} {}'.format(AG_N2LH_END_THREAD, mac)
        ClientN2LH(cmd, url_lh).do(AG_N2LH_PATH_BASE, 1000)


    def test_n2lh_ble_cmd_ans_timeout(self):
        t = calc_n2lh_cmd_ans_timeout_ms(AG_BLE_CMD_CRC)
        print(t)
        assert t == calc_ble_cmd_ans_timeout(CRC_CMD) * 1.1 * 1000
