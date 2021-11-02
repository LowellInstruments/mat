import asyncio
import threading
from bleak import BleakError
from mat.bleak.ble_utils_logger_do2_dummy import cmd_tx, ans_rx
from mat.bleak.ble_engine import ble_engine
from mat.ble_utils_shared import EngineException
import mat.ble_utils_shared as bs


def ble_engine_do2_dummy(q_c, q_a):
    def _f():
        try:
            asyncio.run(ble_engine(q_c, q_a, bs.g_hooks))

        except EngineException as ex:
            print('\t\t(en) exception: {}'.format(ex))
            q_a.put(bs.ENGINE_CMD_EXC)

        except BleakError as ox:
            print('\t\t(en) BLE exception: {}'.format(ox))
            q_a.put(bs.ENGINE_CMD_EXC)

    print('starting ble_engine_do2_dummy...')
    bs.g_hooks['uuid_c'] = None
    bs.g_hooks['cmd_cb'] = cmd_tx
    bs.g_hooks['ans_cb'] = ans_rx
    bs.g_hooks['names'] = None

    return threading.Thread(target=_f)
