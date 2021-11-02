import time
from mat.bluepy.ble_xmlrpc_server import xs_run
from mat.bluepy.ble_xmlrpc_client import XS_DEFAULT_PORT, xc_run, run_thread


def xr_launch_threads(q_cmd, q_ans):

    # queues are only for client
    u = 'http://localhost:{}'.format(XS_DEFAULT_PORT)
    run_thread(xc_run, u, q_cmd, None, q_ans)
    run_thread(xs_run)

    # give time to BLE XML RPC threads to start
    time.sleep(.1)
