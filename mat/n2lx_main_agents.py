import threading

from mat.n2lh_agent import PORT_N2LH, AgentN2LH
from mat.n2ll_agent import AgentN2LL


def _url_ll():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


url_lh = 'tcp4://localhost:{}'.format(PORT_N2LH)
url_ll = _url_ll()


# running this on Rpi / BASH may need root and:
# PRE_REQ=/usr/lib/arm-linux-gnueabihf/libatomic.so.1
# sudo LD_PRELOAD=$PRE_REQ python3 n2lx_main_agents.py


if __name__ == '__main__':
    ag_n2lh = AgentN2LH(url_lh)
    ag_n2ll = AgentN2LL(url_ll)
    th_ag_n2lh = threading.Thread(target=ag_n2lh.loop_n2lh_agent)
    th_ag_n2ll = threading.Thread(target=ag_n2ll.loop_n2ll_agent)
    th_ag_n2lh.start()
    th_ag_n2ll.start()
    print('main_agents thread exits')
