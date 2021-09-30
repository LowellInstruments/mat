import asyncio
import threading
from bleak import BleakClient, BleakScanner, BleakError
from mat.ble_commands import *
from mat.ble_logger_do2_utils import EngineException, ENGINE_CMD_EXC, ENGINE_CMD_BYE, ENGINE_CMD_DISC, ENGINE_CMD_CON, \
    ENGINE_CMD_SCAN


# global variables used in this module
from mat.ble_logger_mat1_utils import UUID, is_rn4020_answer_done

g_ans = bytes()
g_cmd = ''


async def _cmd_wait_ans():

    # leave: at timeout or _nh() says so
    till = 5
    while 1:
        if is_rn4020_answer_done(g_cmd, g_ans):
            print('[ OK ] {}'.format(g_cmd))
            break

        if till == 0:
            break

        print('[ .. ] {}'.format(g_ans))
        await asyncio.sleep(1)
        till -= 1


# notifications handler
async def _nh(_, data):
    global g_ans
    g_ans += bytes(data)
    # print(g_ans)


async def _cmd_send(cli, s):
    # s: 'STS \r'
    s = s.encode()
    i = 0

    # RN4020 needs small chunks of commands < 20 bytes
    while 1:
        _ = s[i:i+10]
        await cli.write_gatt_char(UUID, _)
        i += 10
        if not _:
            break
        await asyncio.sleep(.005)


async def _engine(q_cmd, q_ans):
    """
    loop: send BLE command to logger and receive answer
    """

    cli = None

    while 1:
        # thread: dequeue external command such as 'STS \r'
        global g_cmd
        g_cmd = q_cmd.get()

        # command: special 'quit thread'
        if g_cmd == ENGINE_CMD_BYE:
            if cli:
                await cli.disconnect()
            q_ans.put(b'bye OK')
            break

        # command: special exception COMMAND testing
        if g_cmd.startswith(ENGINE_CMD_EXC):
            raise EngineException(ENGINE_CMD_EXC)

        # command: special 'disconnect', takes ~ 2 seconds
        if g_cmd.startswith(ENGINE_CMD_DISC):
            if cli:
                await cli.disconnect()
            cli = None
            q_ans.put(b'disconnect OK')
            continue

        # command: special 'connect', also enables config descriptor
        if g_cmd.startswith(ENGINE_CMD_CON):
            mac = g_cmd.split()[1]
            cli = BleakClient(mac)

            # RN4020 is slow to connect in noisy environments
            if await cli.connect(timeout=30):
                await cli.start_notify(UUID, _nh)
                q_ans.put(cli.address)
                continue
            cli = None
            continue

        # command: special 'scan'
        if g_cmd.startswith(ENGINE_CMD_SCAN):
            scanner = BleakScanner()
            await scanner.start()
            await asyncio.sleep(5.0)
            await scanner.stop()
            rv = scanner.discovered_devices
            rv = [i.address for i in rv if i.name.startswith('MAT')]
            q_ans.put(rv)
            continue

        # coroutines: send dequeued CMD, enqueue answer back
        global g_ans
        g_ans = bytes()
        tc = _cmd_send(cli, g_cmd)
        await asyncio.gather(tc)
        await _cmd_wait_ans()
        q_ans.put(g_ans)


def __engine(q_cmd, q_ans):
    try:
        print('starting ble_engine_mat1...')
        asyncio.run(_engine(q_cmd, q_ans))

    except EngineException as ex:
        print('\t\t(en) exception in BLE engine: {}'.format(ex))
        q_ans.put(ENGINE_CMD_EXC)

    except BleakError as ox:
        print('\t\t(en) exception in BLE engine: {}'.format(ox))
        q_ans.put(ENGINE_CMD_EXC)


# called at logger controller's constructor
def ble_engine_mat1(q_in, q_out):

    # thread BLE engine
    th = threading.Thread(target=__engine, args=(q_in, q_out, ))
    th.start()



