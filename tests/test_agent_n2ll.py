from mat.agent_n2ll import AgentN2LL


def _u():
    url = 'amqps://{}:{}/{}'
    _user = 'dfibpovr'
    _rest = 'rqMn0NIFEjXTBtrTwwgRiPvcXqfCsbw9@chimpanzee.rmq.cloudamqp.com'
    return url.format(_user, _rest, _user)


if __name__ == '__main__':
    u_l = _u()

    ag_n2ll = AgentN2LL(u_l, threaded=0)
    ag_n2ll.start()
