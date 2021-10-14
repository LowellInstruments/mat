import asyncio
import mat.bleak.ble_utils_shared as bs


UUID_C = '569a2000-b87f-490c-92cb-11ba5ea5167c'
UUID_W = '569a2001-b87f-490c-92cb-11ba5ea5167c'


async def cmd_tx(cli, s):
    # s: '*EA123'
    return await cli.write_gatt_char(UUID_W, s.encode())


async def ans_rx():
    c = bs.g_cmd
    m = {
        # 'file_info': (10, c.encode()),
        # todo: 10 works for small file downloads
        # you must calculate the timeout for big ones
        # 'file_get': (10, b'*0005D\x00')
    }

    # default 5 seconds
    till = 50
    while till:
        a = bs.g_ans

        if c == '*EA123' and a == b'*Xa{"Authenticated":true}':
            break
        if c.startswith('*LT') and c[3:].encode() in a:
            # a: b'*0020t\x00{"Synchronized":1634224146}'
            break
        if c.startswith('*BF') and b'ArchiveBit' in a:
            # a: b'..."ArchiveBit":"+"}'
            break

        # todo >> do the file saving one

        till -= 1
        await asyncio.sleep(.1)
