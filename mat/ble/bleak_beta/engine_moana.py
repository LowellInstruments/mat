import asyncio

import mat.ble.bleak_beta.engine_base_utils as ebu
from mat.ble.bleak_beta.engine_base import engine


UUID_C = '569a2000-b87f-490c-92cb-11ba5ea5167c'
UUID_W = '569a2001-b87f-490c-92cb-11ba5ea5167c'


def engine_moana(q_c, q_a):
    print('starting bleak BLE engine_moana...')
    ebu.g_hooks['uuid_c'] = UUID_C
    ebu.g_hooks['cmd_cb'] = cmd_tx
    ebu.g_hooks['ans_cb'] = ans_rx
    ebu.g_hooks['names'] = ('ZT-MOANA-0051', )
    engine(q_c, q_a, ebu.g_hooks)


async def cmd_tx(cli, s):
    # s: '*EA123'
    return await cli.write_gatt_char(UUID_W, s.encode())


# todo > copy this from bluepy implementation
async def ans_rx():
    c = ebu.g_cmd
    m = {
    }

    # default 5 seconds
    till = 50
    while till:
        a = ebu.g_ans

        if c == '*EA123' and a == b'*Xa{"Authenticated":true}':
            break
        if c.startswith('*LT') and c[3:].encode() in a:
            # a: b'*0020t\x00{"Synchronized":1634224146}'
            break
        if c.startswith('*BF') and b'ArchiveBit' in a:
            # a: b'..."ArchiveBit":"+"}'
            break

        till -= 1
        await asyncio.sleep(.1)
