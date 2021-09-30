from mat.ble_commands import BTC_CMD
from mat.logger_controller import STATUS_CMD, TIME_CMD, SET_TIME_CMD, DIR_CMD

# RN4020 constants
UUID = '00035b03-58e6-07dd-021a-08123a000301'


def is_rn4020_answer_done(cmd, ans):

    done = False
    tag = cmd.split()[0]
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

    # debug
    s = '\t\t(en) dbg_rn4020: tag {} ans_len {} g_ans_done {}'
    print(s.format(tag, len(ans), done))

    return done


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
