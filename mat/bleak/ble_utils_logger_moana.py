import asyncio
import mat.bleak.ble_utils_shared as bs


UUID_C = '569a2000-b87f-490c-92cb-11ba5ea5167c'
UUID_W = '569a2001-b87f-490c-92cb-11ba5ea5167c'


async def ans_rx():
    c = bs.g_cmd
    m = {
        #'auth': (10, b'*Xa{"Authenticated":true}'),
        # 'time_sync': (10, c.encode()),
        # 'file_info': (10, c.encode()),
        # todo: 10 works for small file downloads
        # you must calculate the timeout for big ones
        # 'file_get': (10, b'*0005D\x00')
    }

    # default 5 seconds
    till = 50
    while till:
        a = bs.g_ans
        # todo: copy the rest from bluepy moana

        if c == '*EA123' and a == b'*Xa{"Authenticated":true}':
            break
        if c.startswith('*LT') and a[3:] == c[3:].encode():
            break
        till -= 1
        await asyncio.sleep(.1)


async def cmd_tx(cli, s):
    # s: '*EA123'
    return await cli.write_gatt_char(UUID_W, s.encode())
