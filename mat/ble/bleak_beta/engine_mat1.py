from mat.ble.bleak_beta.engine import engine
from mat.ble.bleak_beta.engine_mat1_utils import cmd_tx, ans_rx, UUID_C
import mat.ble.bleak_beta.ble_utils_engine as be


def engine_mat1(q_c, q_a):
    print('starting bleak BLE engine_mat1...')
    be.g_hooks['uuid_c'] = UUID_C
    be.g_hooks['cmd_cb'] = cmd_tx
    be.g_hooks['ans_cb'] = ans_rx
    be.g_hooks['names'] = ('MATP-2W', )
    engine(q_c, q_a, be.g_hooks)
