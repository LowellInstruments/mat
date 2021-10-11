import asyncio
import threading
from bleak import BleakError
from mat.bleak.ble_logger_do2_utils import cmd_tx, ans_rx
from mat.bleak.ble_engine import ble_engine, ENGINE_CMD_EXC
from mat.bleak.ble_shared import EngineException


def ble_engine_do2(q_c, q_a):
    def _f():
        try:
            asyncio.run(ble_engine(q_c, q_a, cmd_tx, ans_rx))

        except EngineException as ex:
            print('\t\t(en) exception: {}'.format(ex))
            q_a.put(ENGINE_CMD_EXC)

        except BleakError as ox:
            print('\t\t(en) BLE exception: {}'.format(ox))
            q_a.put(ENGINE_CMD_EXC)

    print('starting ble_engine_do2...')
    return threading.Thread(target=_f)
