import time
import bluepy
from mat.bluepy.ble_bluepy import ble_linux_write_parameters_as_fast
from mat.ble_commands import ERR_MAT_ANS
from mat.logger_controller import (
    STATUS_CMD, FIRMWARE_VERSION_CMD, LOGGER_INFO_CMD, LOGGER_INFO_CMD_W,
    STOP_CMD, DO_SENSOR_READINGS_CMD, TIME_CMD, SET_TIME_CMD, DIR_CMD, DEL_FILE_CMD,
    LOGGER_HSA_CMD_W, CALIBRATION_CMD, SD_FREE_SPACE_CMD, RESET_CMD, REQ_FILE_NAME_CMD
)


# RN4020 services and chars UUIDs
UUID_S = '00035b03-58e6-07dd-021a-08123a000300'
UUID_C = '00035b03-58e6-07dd-021a-08123a000301'


class LCBLERN4020Delegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)
        self.buf = bytes()

    def handleNotification(self, c_handle, data):
        self.buf += data

    def clear_buf(self):
        self.buf = bytes()


def ble_cmd_estimate_answer_timeout(tag):
    return 10


def ble_cmd_wait_answer(lc, tag, t, q):
    """
    enqueues the result of waiting for a command answer
    :param lc: logger controller BLE object
    :param tag: command tag such as 'STS'
    :param t: timeout
    :param q: queue to push the result to
    :return:
    """

    t += time.perf_counter()
    while 1:
        if time.perf_counter() > t:
            break
        if lc.per.waitForNotifications(0.001):
            t += 0.001
        if _ble_cmd_wait_answer_end(tag, lc.dlg.buf):
            break
    q.put(lc.dlg.buf)
    lc.dlg.clear_buf()


def _ble_cmd_wait_answer_end(tag, partial_answer):  # pragma: no cover
    """ finishes last command wait-for-answer timeout """

    # helper function: identifies a complete answer
    def _exp(ans_buf, simplest=0):
        # returns True when answer starts w/ expected answer format
        _ = '{} 00'.format(tag) if simplest else tag
        return ans_buf.startswith(_)

    # helper function: returns None on unknown tag
    def _ans_unk(_tag):
        print('unknown tag {}'.format(_tag))
        # don't remove: albeit maybe redundant, it makes it clear
        return None

    # convert answer, in case it is needed
    b = partial_answer
    try:
        # bytes -> string
        a = b.decode()
    except UnicodeError:
        # don't convert -> DWL answer remains bytes
        tag = 'DWL'
        a = b

    # early leave when error or invalid command
    if a.startswith(ERR_MAT_ANS) or a.startswith('INV'):
        time.sleep(.5)
        # don't remove, indicates we are done
        return True

    # command leaves early (el) when we recognize proper answer
    _el = {
        DIR_CMD: lambda: b.endswith(b'\x04\n\r') or b.endswith(b'\x04'),
        STATUS_CMD: lambda: _exp(a) and len(a) == 8,
        FIRMWARE_VERSION_CMD: lambda: _exp(a) and len(a) == 6 + 6,
        TIME_CMD: lambda: _exp(a) and len(a) == 6 + 19,
        SET_TIME_CMD: lambda: _exp(a),
        STOP_CMD: lambda: _exp(a) or (_exp(a) and len(a) == 8),
        # RUN_CMD: lambda: _exp(a),
        # RWS_CMD: lambda: _exp(a),
        # SWS_CMD: lambda: _exp(a),
        # SENSOR_READINGS_CMD: lambda: _exp(a) and (len(a) == 6 + 40),
        REQ_FILE_NAME_CMD: lambda: _exp(a) or a.endswith('.lid'),
        LOGGER_INFO_CMD: lambda: _exp(a) and len(a) <= 6 + 7,
        LOGGER_INFO_CMD_W: lambda: _exp(a),
        SD_FREE_SPACE_CMD: lambda: _exp(a) and len(a) == 6 + 8,
        DEL_FILE_CMD: lambda: _exp(a),
        DO_SENSOR_READINGS_CMD: lambda: _exp(a) and (len(a) == 6 + 12),
        CALIBRATION_CMD: lambda: _exp(a) and (len(a) == 6 + 8),
        RESET_CMD: lambda: _exp(a),
        LOGGER_HSA_CMD_W: lambda: _exp(a)
        # download commands (DWG / DWL) do NOT use all this)
    }
    _el.setdefault(tag, lambda: _ans_unk(tag))
    # returns True or False
    return _el[tag]()


def ble_cmd_build(*args):
    # phone commands use aggregated, a.k.a. transparent, mode
    # they do NOT follow LI proprietary format (DWG NNABCD...)
    tp_mode = len(str(args[0]).split(' ')) > 1
    cmd = str(args[0])
    if tp_mode:
        to_send = cmd
    else:
        # build LI proprietary command format
        cmd = str(args[0])
        arg = str(args[1]) if len(args) == 2 else ''
        n = '{:02x}'.format(len(arg)) if arg else ''
        to_send = cmd + ' ' + n + arg
    to_send += chr(13)

    print(to_send)

    # know command tag, ex: 'STP'
    tag = cmd[:3]
    return to_send, tag


def ble_connect_to_rn4020_logger(lc):
    assert ble_linux_write_parameters_as_fast(lc.h)

    till = 10
    retries = 3
    for i in range(retries):
        try:
            lc.per = bluepy.btle.Peripheral(lc.mac, iface=lc.h, timeout=till)
            lc.per.setDelegate(lc.dlg)
            lc.svc = lc.per.getServiceByUUID(UUID_S)
            print(lc.svc)
            lc.cha = lc.svc.getCharacteristics(UUID_C)[0]
            desc = lc.cha.valHandle + 1
            print(desc)
            lc.per.writeCharacteristic(desc, b'\x01\x00')
            return lc

        except (AttributeError, bluepy.btle.BTLEException) as ex:
            e = '[ BLE ] can\'t connect {} / {}: {}'
            print(e.format(i + 1, retries, ex))


def ble_file_list_as_dict(ls, ext, match=True):
    if ls is None:
        return {}

    err = ERR_MAT_ANS.encode()
    if err in ls:
        return err

    if type(ext) is str:
        ext = ext.encode()

    files, idx = {}, 0

    # ls: b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r\n\rMAT.cfg\t\t\t189\n\r\x04\n\r'
    ls = ls.split()
    while idx < len(ls):
        name = ls[idx]
        if name in [b'\x04']:
            break

        # wild-card case
        if ext == b'*' and name not in [b'.', b'..']:
            files[name.decode()] = int(ls[idx + 1])
        # specific extension case
        elif name.endswith(ext) == match and name not in [b'.', b'..']:
            files[name.decode()] = int(ls[idx + 1])
        idx += 2
    return files


def ble_cmd_file_list_only_lid_files(lc) -> dict:
    return lc.ble_cmd_dir_ext(b'lid')

