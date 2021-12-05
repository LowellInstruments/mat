import asyncio
from mat.logger_controller_ble import BTC_CMD, GET_FILE_CMD
from mat.logger_controller import STATUS_CMD, TIME_CMD, SET_TIME_CMD, DIR_CMD
from mat.ble.bleak_beta.engine_base import engine
import mat.ble.bleak_beta.engine_base_utils as ebu


UUID_C = '00035b03-58e6-07dd-021a-08123a000301'


def engine_mat(q_c, q_a):
    print('starting bleak BLE engine_mat...')
    ebu.g_hooks['uuid_c'] = UUID_C
    ebu.g_hooks['cmd_cb'] = cmd_tx
    ebu.g_hooks['ans_cb'] = ans_rx
    ebu.g_hooks['names'] = ('MATP-2W',)
    engine(q_c, q_a, ebu.g_hooks)


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

    # s = '    debug -> tag rn4020 {} len {} done {}'
    # print(s.format(tag, len(ans), done))

    return done


async def ans_rx():
    # 10 seconds timeout, steps 10 millis (.01)
    till = 100
    while till:
        if _is_answer_done(ebu.g_cmd, ebu.g_ans):
            break
        # .1 == xmodem speed 4.8, .01 == 5.5
        await asyncio.sleep(.01)
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
