import asyncio
import threading
from bleak import BleakError
from mat.bleak.ble_utils_logger_do2 import cmd_tx, ans_rx, UUID_C
from mat.bleak.ble_engine import ble_engine, ENGINE_CMD_EXC
from mat.bleak.ble_utils_shared import EngineException
import mat.bleak.ble_utils_shared as bs


def ble_engine_do2(q_c, q_a):
    def _f():
        try:
            asyncio.run(ble_engine(q_c, q_a, bs.g_hooks))

        except EngineException as ex:
            print('\t\t(en) exception: {}'.format(ex))
            q_a.put(ENGINE_CMD_EXC)

        except BleakError as ox:
            print('\t\t(en) BLE exception: {}'.format(ox))
            q_a.put(ENGINE_CMD_EXC)

    print('starting ble_engine_do2...')
    bs.g_hooks['uuid_c'] = UUID_C
    bs.g_hooks['cmd_cb'] = cmd_tx
    bs.g_hooks['ans_cb'] = ans_rx
    bs.g_hooks['names'] = ('DO-1', 'DO-2')
    return threading.Thread(target=_f)
