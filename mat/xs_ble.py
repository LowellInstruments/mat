from mat.logger_controller_ble import ble_scan


# will import this file after all is done from XS for file splitting :)
def xs_ble_check_ans_is_ok(s) -> tuple:
    if not s:
        return False, None
    elif s == [b'INV']:
        return False, 'invalid'
    elif s == [b'ERR']:
        return False, 'error'
    return True, s


