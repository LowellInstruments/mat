def xs_ble_check_ans_is_ok(s) -> tuple:
    if not s:
        return False, None
    elif s == [b'INV']:
        return False, 'invalid'
    elif s == [b'ERR']:
        return False, 'error'
    return True, s


