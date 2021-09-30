import asyncio
import threading
from bleak import BleakClient, BleakError, BleakScanner
from mat.bleak.ble_commands import *
from mat.bleak.ble_logger_do2_utils import UUID_W, ENGINE_CMD_BYE, ENGINE_CMD_DISC, ENGINE_CMD_CON, MAX_MTU_SIZE, \
    ENGINE_CMD_SCAN, UUID_C, ENGINE_CMD_EXC, is_answer_done, EngineException

# global variables used in this module
from mat.logger_controller import RUN_CMD, RWS_CMD, SWS_CMD, STOP_CMD

g_ans = bytes()
g_cmd = ''


async def _cmd_wait_ans():

    # estimate time as units of 10 milliseconds
    units = .01
    global g_cmd
    tag = g_cmd.split()[0]
    _ = {
        # 3000 * 10 ms = 30 s
        MY_TOOL_SET_CMD: 3000,
        RUN_CMD: 1500,
        RWS_CMD: 1500,
        SWS_CMD: 1500,
        STOP_CMD: 1500,
    }
    # default: 300 * 10 ms = 3 s
    till = _.get(tag, 300)

    # leave: at timeout or _nh() says so
    while 1:
        if is_answer_done(g_cmd, g_ans):
            print('[ OK ] {}'.format(g_cmd))
            break
        if till == 0:
            break
        if till % 500 == 0:
            print('[ .. ] {}'.format(g_cmd))
        await asyncio.sleep(units)
        till -= 1


# notifications handler
async def _nh(_, data):
    global g_ans
    g_ans += data


async def _cmd_send(cli, s):
    # s: 'STS \r'
    return await cli.write_gatt_char(UUID_W, s.encode())


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
            cli._mtu_size = MAX_MTU_SIZE
            if await cli.connect():
                await cli.start_notify(UUID_C, _nh)
                q_ans.put(cli.address)
                continue
            cli = None
            continue

        # command: special 'scan'
        if g_cmd.startswith(ENGINE_CMD_SCAN):
            scanner = BleakScanner()
            await scanner.start()
            await asyncio.sleep(4.0)
            await scanner.stop()
            rv = scanner.discovered_devices
            valid_names = ('DO-1', 'DO-2')
            rv = [i.address for i in rv if i.name in valid_names]
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
        print('starting ble_engine_do2...')
        asyncio.run(_engine(q_cmd, q_ans))

    except EngineException as ex:
        print('\t\t(en) exception in BLE engine: {}'.format(ex))
        q_ans.put(ENGINE_CMD_EXC)

    except BleakError as ox:
        print('\t\t(en) exception in BLE engine: {}'.format(ox))
        q_ans.put(ENGINE_CMD_EXC)


# called at logger controller's constructor
def ble_engine_do2(q_in, q_out):

    # thread BLE engine
    th = threading.Thread(target=__engine, args=(q_in, q_out, ))
    th.start()



