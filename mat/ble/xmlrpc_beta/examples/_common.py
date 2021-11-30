import time
from mat.ble.xmlrpc_beta.xmlrpc_lc_ble_client import XS_DEFAULT_PORT, run_thread, xc_run
from mat.ble.xmlrpc_beta.xmlrpc_lc_ble_server import xs_run


def xr_launch_threads(q_cmd, q_ans):

    # queues are only for client
    u = 'http://localhost:{}'.format(XS_DEFAULT_PORT)
    run_thread(xc_run, u, q_cmd, None, q_ans)
    run_thread(xs_run)

    # give time to BLE XML RPC threads to start
    time.sleep(.1)
