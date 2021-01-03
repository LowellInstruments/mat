from mat.agent_n2lh import PORT_N2LH, AgentN2LH
from mat.agent_n2ll import AgentN2LL


def _url_ll():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)
url_lh = 'tcp4://localhost:{}'.format(PORT_N2LH)
url_ll = _url_ll()



# running this on Rpi / BASH may need root and:
# PRE_REQ=/usr/lib/arm-linux-gnueabihf/libatomic.so.1
# LD_PRELOAD=$PRE_REQ python3 main_nle_s.py


if __name__ == '__main__':
    ag_n2lh = AgentN2LH(url_lh)
    ag_n2ll = AgentN2LL(url_ll)
    ag_n2lh.start()
    ag_n2ll.start()
    ag_n2lh.join(timeout=1)
    ag_n2lh.join(timeout=1)
    print('main_agents thread exists')