import threading
import time

from mat.n2lx_utils import *


def _p(s):
    print(s, flush=True)


class AgentN2LH_Dummy(threading.Thread):
    def __init__(self, q1):
        """ creates a dummy agent which notifies """
        super().__init__()
        self.q_notification = q1

    def loop_ag_dummy(self):
        i = 0
        while 1:
            # s -> 'ntf dummy X'
            s = '{} dummy test #{}'.format(AG_N2LH_NOTIFICATION, i)
            self.q_notification.put(s)
            time.sleep(10)
            i += 1

    def run(self):
        self.loop_ag_dummy()
        _p('AG_DUMMY thread ends')
