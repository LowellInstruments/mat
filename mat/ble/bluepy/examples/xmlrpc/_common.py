import threading
import time
from mat.ble.bluepy.xc_ble_lowell import XS_DEFAULT_PORT, xc_run
from mat.ble.bluepy.xs_ble_lowell import xs_run


def xr_launch_threads(q_cmd, q_ans):

    u = 'http://localhost:{}'.format(XS_DEFAULT_PORT)
    c_args = (u, q_cmd, q_ans, )
    th = threading.Thread(target=xc_run, args=c_args)
    th.start()
    th = threading.Thread(target=xs_run)
    th.start()

    # give time threads to start
    time.sleep(.1)
