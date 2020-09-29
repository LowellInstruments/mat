from mat.examples_ble_rn4020.simple.simple import rn4020_shell
from mat.logger_controller import STOP_CMD


def _grep_lid(_in):
    out = []
    for i, n in enumerate(_in):
        n = str(n.decode())
        if not n.isnumeric():
            continue
        if not int(n) > 0:
            continue
        if not _in[i - 1].endswith(b'.lid'):
            continue
        out.append(_in[i - 1])
        out.append(_in[i])
    return out


# override mac
# mac =


def ls_lid_rn4020():
    ls = rn4020_shell([STOP_CMD, 'DIR'])
    ls = _grep_lid(ls)
    print('\t*.lid -> {}'.format(ls))
    return ls


if __name__ == '__main__':
    ls_lid_rn4020()
