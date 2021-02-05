import threading
import time

from getmac import get_mac_address

from mat.n2ll_agent import AgentN2LL
from mat.n2ll_client import ClientN2LL
from mat.n2lx_utils import AG_N2LL_CMD_BYE


def _u_l():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


class TestAgent_N2LL:
    def test_agent_n2ll_command_bye(self):
        ag_n2ll = AgentN2LL(_u_l())
        th_ag_n2ll = threading.Thread(target=ag_n2ll.loop_n2ll_agent)
        th_ag_n2ll.start()

        # need sleep for agent_N2LL to start
        time.sleep(2)
        cli_n2ll = ClientN2LL(_u_l(), None)
        mac = get_mac_address()
        cmd = '{} {}'.format(AG_N2LL_CMD_BYE, mac)
        cli_n2ll.tx(cmd)
        # need sleep to give time agent_N2LL to answer
        time.sleep(5)
        print(cli_n2ll.dump_cli_rx)
        assert 'bye you by N2LL' in cli_n2ll.dump_cli_rx
        assert mac in cli_n2ll.dump_cli_rx
