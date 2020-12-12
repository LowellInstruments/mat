import threading
import time
import queue
from mat.agent_utils import AG_GPS_CMD_BYE, AG_GPS_ANS_BYE


def _p(s):
    print(s, flush=True)


class AgentGPS(threading.Thread):
    # has one collector thread, one interface thread
    def __init__(self, q_in, q_out, threaded):
        super().__init__()
        self.lat = None
        self.lon = None
        self.ts = None
        self.q_in = q_in
        self.q_out = q_out
        if not threaded:
            self._loop_agent()

    def run(self):
        self._loop_agent()

    def _gps_get(self):
        self.lat = 'my_lat'
        self.lon = 'my_lon'
        self.ts = time.perf_counter()
        return self.lat, self.lon, self.ts

    def _loop_agent(self):
        while 1:
            # measure
            _out = self._gps_get()

            # receive a petition
            try:
                _in = self.q_in.get(timeout=3)
            except queue.Empty:
                continue

            # loop breaker capability
            if _in == AG_GPS_CMD_BYE:
                self.q_out.put(AG_GPS_ANS_BYE)
                break

            # normal answer
            self.q_out.put(_out)


def my_test_agent_gps():
    q_req = queue.Queue()
    q_rep = queue.Queue()
    ag = AgentGPS(q_req, q_rep, threaded=1)
    ag.start()

    # give GPS thread time to boot
    time.sleep(1)

    # ask a couple of GPS measures
    for i in range(3):
        q_req.put(None)
        gps_data = q_rep.get()
        print(gps_data)
        time.sleep(1)

    # force GPS thread to stop
    q_req.put(AG_GPS_CMD_BYE)
    _out = q_rep.get()
    _p(_out)
    ag.join()


if __name__ == '__main__':
    my_test_agent_gps()


