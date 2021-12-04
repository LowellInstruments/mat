import asyncio
from bleak import BleakClient, BleakError
from mat.ble.bleak_beta.engine_base_utils import EngineException, engine_parse_cmd_bye, engine_parse_cmd_disconnect, engine_parse_cmd_scan, engine_parse_cmd_connect
import mat.ble.bleak_beta.engine_base_utils as be
import mat.ble_utils_shared as bs


async def _nh(_, data):
    be.g_ans += data


async def _parse_command(cmd_tx_cb, ans_rx_cb, cli, q):
    be.g_ans = bytes()
    tc = cmd_tx_cb(cli, be.g_cmd)
    await asyncio.gather(tc)
    await ans_rx_cb()
    q.put(be.g_ans)


async def _engine_fxn(q_cmd, q_ans, hooks):
    assert bs.check_bluez_version()

    uuid_c = hooks['uuid_c']
    cmd_tx_cb = hooks['cmd_cb']
    ans_rx_cb = hooks['ans_cb']
    nn = hooks['names']
    cli = None

    while 1:
        # dequeue external command
        be.g_cmd = q_cmd.get()

        # xmodem case apart :)
        if await be.engine_parse_xmodem(be.g_cmd):
            await _parse_command(cmd_tx_cb, ans_rx_cb, cli, q_ans)
            continue

        if await engine_parse_cmd_bye(be.g_cmd, cli, q_ans):
            break

        if await engine_parse_cmd_scan(be.g_cmd, nn, q_ans):
            continue

        if engine_parse_cmd_disconnect(be.g_cmd, q_ans):
            if cli:
                await cli.disconnect()
            cli = None
            continue

        if engine_parse_cmd_connect(be.g_cmd):
            mac = be.g_cmd.split()[1]
            cli = BleakClient(mac, timeout=30)
            if await cli.connect():
                # todo > study this hardcoded
                MAX_MTU_SIZE = 247
                cli._mtu_size = MAX_MTU_SIZE
                await asyncio.sleep(1.1)
                await cli.start_notify(uuid_c, _nh)
                q_ans.put(cli.address)
            else:
                cli = None
            continue

        await _parse_command(cmd_tx_cb, ans_rx_cb, cli, q_ans)


# generic bleak BLE engine
def engine(q_c, q_a, h):
    try:
        asyncio.run(_engine_fxn(q_c, q_a, h))

    except EngineException as ex:
        print('\t\t(en) exception: {}'.format(ex))
        q_a.put(be.ENGINE_CMD_EXC)

    except BleakError as ox:
        print('\t\t(en) BLE exception: {}'.format(ox))
        q_a.put(be.ENGINE_CMD_EXC)
