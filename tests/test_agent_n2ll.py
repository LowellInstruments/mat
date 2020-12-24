import time

from getmac import get_mac_address

from mat.agent_n2ll import AgentN2LL, ClientN2LL
from mat.agent_utils import AG_N2LL_CMD_BYE


def _u():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


class TestAgent_N2LL:
    def test_agent_n2ll_command_bye(self):
        u_l = _u()
        ag_n2ll = AgentN2LL(u_l, threaded=1)
        ag_n2ll.start()
        # need sleep for agent_N2LL to start
        time.sleep(2)
        cli_n2ll = ClientN2LL(u_l, None)
        mac = get_mac_address()
        cmd = '{} {}'.format(AG_N2LL_CMD_BYE, mac)
        cli_n2ll.tx(cmd)
        # need sleep to give time agent_N2LL to answer
        time.sleep(5)
        print(cli_n2ll.dump_cli_rx)
        assert 'bye you by N2LL' in cli_n2ll.dump_cli_rx
        assert mac in cli_n2ll.dump_cli_rx
