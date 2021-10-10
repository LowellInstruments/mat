import asyncio
import threading
from bleak import BleakClient, BleakError, BleakScanner
from mat.bleak.ble_commands import *
from mat.bleak.ble_logger_do2_utils import UUID_W, ENGINE_CMD_BYE, ENGINE_CMD_DISC, ENGINE_CMD_CON, MAX_MTU_SIZE, \
    ENGINE_CMD_SCAN, UUID_C, ENGINE_CMD_EXC, EngineException, ans_rx
import mat.bleak.ble_shared as bs


async def _nh(_, data):
    bs.g_ans += data


async def _cmd_tx(cli, s):
    # s: 'STS \r'
    return await cli.write_gatt_char(UUID_W, s.encode())


async def _engine(q_cmd, q_ans):
    """
    loop: send BLE command to logger and receive answer
    """

    cli = None

    while 1:
        # thread: dequeue external command such as 'STS \r'
        bs.g_cmd = q_cmd.get()

        # command: special 'quit thread'
        if bs.g_cmd == ENGINE_CMD_BYE:
            if cli:
                await cli.disconnect()
            q_ans.put(b'bye OK')
            break

        # command: special exception COMMAND testing
        if bs.g_cmd.startswith(ENGINE_CMD_EXC):
            raise EngineException(ENGINE_CMD_EXC)

        # command: special 'disconnect', takes ~ 2 seconds
        if bs.g_cmd.startswith(ENGINE_CMD_DISC):
            if cli:
                await cli.disconnect()
            cli = None
            q_ans.put(b'disconnect OK')
            continue

        # command: special 'connect', also enables config descriptor
        if bs.g_cmd.startswith(ENGINE_CMD_CON):
            mac = bs.g_cmd.split()[1]
            cli = BleakClient(mac)
            cli._mtu_size = MAX_MTU_SIZE
            if await cli.connect():
                await cli.start_notify(UUID_C, _nh)
                q_ans.put(cli.address)
                continue
            cli = None
            continue

        # command: special 'scan'
        if bs.g_cmd.startswith(ENGINE_CMD_SCAN):
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
        bs.g_ans = bytes()
        tc = _cmd_tx(cli, bs.g_cmd)
        await asyncio.gather(tc)
        await ans_rx()
        q_ans.put(bs.g_ans)


def ble_engine_do2(q_cmd, q_ans):
    def _f():
        try:
            asyncio.run(_engine(q_cmd, q_ans))

        except EngineException as ex:
            print('\t\t(en) exception in BLE engine: {}'.format(ex))
            q_ans.put(ENGINE_CMD_EXC)

        except BleakError as ox:
            print('\t\t(en) exception in BLE engine: {}'.format(ox))
            q_ans.put(ENGINE_CMD_EXC)

    print('starting ble_engine_do2...')
    th = threading.Thread(target=_f)
    th.start()



