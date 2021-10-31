import asyncio
from mat.logger_controller_ble_cmd import BTC_CMD, GET_FILE_CMD
from mat.logger_controller import STATUS_CMD, TIME_CMD, SET_TIME_CMD, DIR_CMD
import mat.ble_utils_shared as bs


UUID_C = '00035b03-58e6-07dd-021a-08123a000301'


def ble_cmd_dir_result_as_dict_rn4020(ls: bytes) -> dict:
    if b'ERR' in ls:
        return {'ERR': 0}

    # ls: b'\n\rSystem Volume Information\t\t\t0\n\rMAT.cfg\t\t\t208\n\r\x04\n\r'
    d = {}
    i = 0
    ls = ls.split(b'\n\r')

    # ls: [b'', b'System Volume Information\t\t\t0', b'MAT.cfg\t\t\t208', b'\x04', b'']
    for i in ls:
        if i == b'':
            continue
        if i == b'\x04':
            break
        name, size = i.decode().split('\t\t\t')
        d[name] = int(size)
    # d: { 'MAT.cfg': 189 }
    return d


def _is_answer_done(cmd, ans):

    done = False
    tag = cmd.split()[0]

    if tag == b'XMD':
        done = len(ans) == 1029
        return done

    tan = ans[2:5].decode()

    if tan == tag == STATUS_CMD and len(ans) == 12:
        done = True
    if tan == tag == TIME_CMD and len(ans) == 29:
        done = True
    if tag == BTC_CMD and len(ans) == 18:
        done = True
    if tan == tag == SET_TIME_CMD and len(ans) == 10:
        done = True
    if tag == DIR_CMD and ans.endswith(b'\x04\n\r'):
        done = True
    if tag == GET_FILE_CMD and ans == b'\n\rGET 00\r\n':
        done = True

    # debug
    s = '    dbg: tag {} len {} done {}'
    print(s.format(tag, len(ans), done))

    return done


async def ans_rx():
    # 5 seconds timeout
    till = 50
    while till:
        if _is_answer_done(bs.g_cmd, bs.g_ans):
            break
        # .1 == xmodem speed 4.8, .01 == 5.5
        await asyncio.sleep(.1)
        till -= 1


async def cmd_tx(cli, s):
    # RN4020-based loggers XMODEM
    if s[:4] == b'XMD ':
        s = s[4:]
        await cli.write_gatt_char(UUID_C, s)
        return

    # s: 'STS \r', n: chunk size
    s = s.encode()
    n = 10
    for _ in (s[i:i+n] for i in range(0, len(s), n)):
        await cli.write_gatt_char(UUID_C, _)
