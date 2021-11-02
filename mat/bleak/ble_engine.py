import asyncio
from bleak import BleakClient
from mat.bleak.ble_utils_logger_do2 import MAX_MTU_SIZE
from mat.ble_utils_shared import engine_parse_cmd_bye, engine_parse_cmd_connect, engine_parse_cmd_disconnect, \
    engine_parse_cmd_scan, engine_parse_cmd_exception
import mat.ble_utils_shared as bs


async def _nh(_, data):
    bs.g_ans += data


async def _step(cmd_tx_cb, ans_rx_cb, cli, q):
    bs.g_ans = bytes()
    tc = cmd_tx_cb(cli, bs.g_cmd)
    await asyncio.gather(tc)
    await ans_rx_cb()
    q.put(bs.g_ans)


async def ble_engine(q_cmd, q_ans, hooks):
    assert bs.check_bluez_version()

    uuid_c = hooks['uuid_c']
    cmd_tx_cb = hooks['cmd_cb']
    ans_rx_cb = hooks['ans_cb']
    nn = hooks['names']
    cli = None

    while 1:
        # dequeue external command
        bs.g_cmd = q_cmd.get()

        # xmodem case apart :)
        if await bs.engine_parse_xmodem(bs.g_cmd):
            await _step(cmd_tx_cb, ans_rx_cb, cli, q_ans)
            continue

        if await engine_parse_cmd_bye(bs.g_cmd, cli, q_ans):
            break

        engine_parse_cmd_exception(bs.g_cmd)

        if await engine_parse_cmd_scan(bs.g_cmd, nn, q_ans):
            continue

        if engine_parse_cmd_disconnect(bs.g_cmd, q_ans):
            if cli:
                await cli.disconnect()
            cli = None
            continue

        if engine_parse_cmd_connect(bs.g_cmd):
            mac = bs.g_cmd.split()[1]
            cli = BleakClient(mac)
            cli._mtu_size = MAX_MTU_SIZE
            if await cli.connect(timeout=10):
                await cli.start_notify(uuid_c, _nh)
                q_ans.put(cli.address)
            else:
                cli = None
            continue

        await _step(cmd_tx_cb, ans_rx_cb, cli, q_ans)

