import asyncio
from bleak import BleakClient, BleakScanner
from mat.bleak.ble_logger_do2_utils import MAX_MTU_SIZE, UUID_C
import mat.bleak.ble_shared as bs


ENGINE_CMD_BYE = 'cmd_bye'
ENGINE_CMD_CON = 'cmd_connect'
ENGINE_CMD_DISC = 'cmd_disconnect'
ENGINE_CMD_SCAN = 'cmd_scan'
ENGINE_CMD_EXC = 'exc_ble_engine'


async def _nh(_, data):
    bs.g_ans += data


async def ble_engine(q_cmd, q_ans, cmd_tx_cb, ans_rx_cb):
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
            raise bs.EngineException(ENGINE_CMD_EXC)

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
        tc = cmd_tx_cb(cli, bs.g_cmd)
        await asyncio.gather(tc)
        await ans_rx_cb()
        q_ans.put(bs.g_ans)
