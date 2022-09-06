import time
import bluepy
from mat.logger_controller import DIR_CMD, RUN_CMD, SWS_CMD, SET_TIME_CMD, STATUS_CMD, TIME_CMD, RWS_CMD, STOP_CMD, \
    LOGGER_INFO_CMD_W, DO_SENSOR_READINGS_CMD, SENSOR_READINGS_CMD
from mat.logger_controller_ble import *


# from www.novelbits.io/bluetooth-5-speed-maximum-throughput/
# BLE MAX PDU size is 255 - 4 B header DLE = 251
# 251 is the value the guys @ TI they use for sysconfig
# 251 - 4 B header L2CAP = 247 = MTU size (including 3 B header ATT)
# so, we set MTU_SIZE 247 here, but 244 as payload in logger
MTU_SIZE = 247


class LCBLELowellDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)
        self.buf = bytes()

    def handleNotification(self, c_handle, data):
        # print(data)
        self.buf += data


def calculate_answer_timeout(tag):
    t = 10
    if tag == MY_TOOL_SET_CMD:
        t = 30
    if tag == TEST_CMD:
        t = 2
    return time.perf_counter() + t


def build_command(*args):
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

    # debug
    # print(to_send.encode())

    # know command tag, ex: 'STP'
    tag = cmd[:3]
    return to_send, tag


def connect_cc26x2r(lc):
    # prevents running all being non-root
    # assert ble_linux_write_parameters_as_fast(lc.h)

    uuid_s = 'f0001130-0451-4000-b000-000000000000'
    uuid_c = 'f0001132-0451-4000-b000-000000000000'
    uuid_w = 'f0001131-0451-4000-b000-000000000000'

    if lc.what == 'DO-X':
        uuid_s = 'f000c0c0-0451-4000-b000-000000000000'
        uuid_c = 'f000c0c2-0451-4000-b000-000000000000'
        uuid_w = 'f000c0c1-0451-4000-b000-000000000000'

    try:
        lc.per = bluepy.btle.Peripheral(lc.mac, iface=lc.h, timeout=10)
        lc.per.setDelegate(lc.dlg)
        lc.svc = lc.per.getServiceByUUID(uuid_s)
        lc.cha = lc.svc.getCharacteristics(uuid_c)[0]
        desc = lc.cha.valHandle + 1
        lc.per.writeCharacteristic(desc, b'\x01\x00')
        lc.per.setMTU(MTU_SIZE)
        lc.cha = lc.svc.getCharacteristics(uuid_w)[0]
        return True

    except (AttributeError, bluepy.btle.BTLEException) as ex:
        print('[ BLE ] cannot connect -> {}'.format(ex))
        return False


def ble_cmd_file_list_only_lid_files(lc) -> dict:
    return lc.ble_cmd_dir_ext(b'lid')


def utils_logger_is_cc26x2r(mac, info: str):
    is_do_1 = 'DO-1' in info
    is_do_2 = 'DO-2' in info
    return is_do_1 or is_do_2


def utils_logger_is_cc26x2r_new(mac, info: str):
    return 'DO-4' in info
