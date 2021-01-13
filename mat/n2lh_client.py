import threading
import time

import pynng

from mat.logger_controller_ble_dummy import FAKE_MAC_CC26X2
from mat.n2lh_agent import PORT_N2LH, AgentN2LH, calc_n2lh_cmd_ans_timeout_ms
from mat.n2lx_utils import AG_BLE_CMD_GET_FILE, AG_BLE_ANS_GET_FILE_OK, AG_BLE_CMD_DWG_FILE, AG_BLE_CMD_QUERY, \
    AG_BLE_CMD_STATUS, AG_BLE_CMD_GET_TIME, AG_BLE_CMD_LS_LID, AG_N2LH_PATH_BLE, AG_BLE_END_THREAD, AG_N2LH_PATH_BASE, \
    AG_N2LH_END_THREAD

N2LH_CLI_SEND_TIMEOUT_MS = 5000


class ClientN2LH():
    """ ClientN2LH  <-- pynng -->  AgentN2LH     <-- queues -->  AgentN2LH_BLE
        ------------------------>  'ble cmd mac'  ------------->  'cmd mac """
    def __init__(self, s, url, fol):
        super().__init__()
        self.cmd = s
        self.url = url
        self.fol = fol

    def do(self, n2lh_path, rx_timeout_ms):
        try:
            return self._do(n2lh_path, rx_timeout_ms)
        except pynng.Timeout:
            return None

    def _do(self, n2lh_path, rx_timeout_ms):
        """ builds and sends N2LH command """
        _c = self.cmd.split(' ')[0]
        sk = pynng.Pair0(send_timeout=N2LH_CLI_SEND_TIMEOUT_MS)
        sk.recv_timeout = int(rx_timeout_ms)
        sk.dial(self.url)

        # sends N2LH command via pynng, wait for answer w/ timeout
        # n2lh_path: AG_N2LH_PATH_BASE, AG_N2LH_PATH_BLE...
        # _o -> 'ble connect <mac>'
        _o = '{} {}'.format(n2lh_path, self.cmd)
        sk.send(_o.encode())
        _in = sk.recv().decode()

        # extra steps in case of requesting files
        if _c in (AG_BLE_CMD_GET_FILE, AG_BLE_CMD_DWG_FILE):
            # did AgentN2LH_BLE GET / DWG successfully
            _in = sk.recv().decode()
            if AG_BLE_ANS_GET_FILE_OK in _in:
                # once GET / DWG worked, receive file from AgentN2LH_BLE
                b = sk.recv()
                filename = self.cmd.split(' ')[1]
                size = self.cmd.split(' ')[3]
                filepath = '{}/{}'.format(self.fol, filename)
                with open(filepath, 'wb') as f:
                    f.write(b)
                    f.truncate(int(size))

        sk.close()
        return _in


# for N2LH testing purposes
if __name__ == '__main__':
    url_lh = 'tcp4://localhost:{}'.format(PORT_N2LH)
    mac = FAKE_MAC_CC26X2
    ag = AgentN2LH(url_lh)
    th_ag_ble = threading.Thread(target=ag.loop_n2lh_agent)
    th_ag_ble.start()

    # give time agent to start
    time.sleep(1)

    # send client commands
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