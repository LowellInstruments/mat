import time

import pynng
from pynng import Pair0

from mat.agent_n2lh import PORT_N2LH, AgentN2LH, calc_n2lh_cmd_ans_timeout
from mat.agent_utils import AG_N2LH_CMD_BYE, AG_BLE_CMD_QUERY, AG_BLE_CMD_STATUS, AG_BLE_CMD_LS_LID, \
    AG_BLE_CMD_GET_TIME, AG_BLE_CMD_BYE, AG_N2LH_PATH_BLE
from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import FAKE_MAC_CC26X2, FAKE_MAC_RN4020, calc_ble_cmd_ans_timeout


# ignore crashes due to threads
class TestAgentN2LH:
    u = 'tcp4://localhost:{}'.format(PORT_N2LH)
    u_ext = 'tcp4://localhost:{}'.format(PORT_N2LH + 1)
    # m = '60:77:71:22:c8:18'
    # m = '60:77:71:22:c8:08'
    # m = FAKE_MAC_RN4020
    m = FAKE_MAC_CC26X2

    def test_constructor(self):
        ag = AgentN2LH(self.u, threaded=1)
        ag.start()
        list_of_cmd = [AG_N2LH_CMD_BYE]
        _fake_client_send_n_wait(self.u, list_of_cmd, 1000, self.m)

    def test_get_ble_file_there_send_it_here(self):
        if self.m in [FAKE_MAC_CC26X2, FAKE_MAC_RN4020]:
            assert True
            return
        ag = AgentN2LH(self.u, threaded=1)
        ag.start()
        list_of_cmd = ['get_file 2006671_low_20201004_132205.lid . 299950']
        _fake_client_send_n_wait(self.u, list_of_cmd, 1000, self.m)
        # on testing, use 2 sockets, on production, we'll see
        sk = Pair0()
        sk.listen(self.u_ext)
        sk.recv_timeout = 1000
        rv = _fake_client_rx_file(sk, '2006671_low_20201004_132205.lid', 299950)
        sk.close()
        assert rv

    def test_fw_commands(self):
        ag = AgentN2LH(self.u, threaded=1)
        ag.start()
        list_of_cmd = [AG_BLE_CMD_QUERY,
                       AG_BLE_CMD_STATUS,
                       AG_BLE_CMD_GET_TIME,
                       AG_BLE_CMD_LS_LID,
                       AG_BLE_CMD_QUERY,
                       AG_BLE_CMD_BYE]
        # recall time to BLE connect > 1 s
        _fake_client_send_n_wait(self.u, list_of_cmd, 5000, self.m)

    def test_n2lh_cmd_ans_timeout(self):
        t = calc_n2lh_cmd_ans_timeout(AG_BLE_CMD_STATUS)
        assert t == calc_ble_cmd_ans_timeout(STATUS_CMD) * 1.1


def _fake_client_rx_file(sk, filename, size):
    b = sk.recv()
    filename = '_rut_{}'.format(filename)
    with open(filename, 'wb') as f:
        f.write(b)
        f.truncate(int(size))
    sk.close()
    return len(b) == int(size)


def _fake_client_send_n_wait(_url, list_out, timeout_ms: int, mac):
    """ use for testing, on production, N2LH already uses a timeout-ed loop """
    _ = pynng.Pair0(send_timeout=timeout_ms)
    _.recv_timeout = timeout_ms
    _.dial(_url)
    now = time.perf_counter()
    for o in list_out:
        o = '{} {} {}'.format(AG_N2LH_PATH_BLE, o, mac)
        _.send(o.encode())
        _in = _.recv()
        print('\t{}'.format(_in.decode()))
    print('done in {}'.format(time.perf_counter() - now))
    _.close()
