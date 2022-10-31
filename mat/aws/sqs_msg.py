import datetime
import subprocess as sp
from mat.utils import linux_is_rpi3, linux_is_rpi4
import os


SQS_DDH_BOOT = 'DDH_BOOT'
SQS_DDH_ERROR_BLE_HW = 'DDH_ERROR_BLE_HARDWARE'
SQS_LOGGER_DL_OK = 'LOGGER_DOWNLOAD'
SQS_LOGGER_ERROR_OXYGEN = 'LOGGER_ERROR_OXYGEN'
SQS_LOGGER_MAX_ERRORS = 'LOGGER_ERRORS_MAXED_RETRIES'


def sqs_build_msg(rz, lat, lon, vn, dch, m_ver=1):

    # checks
    box_sn = os.getenv('DDH_BOX_SERIAL_NUMBER')

    # todo ---> add box_sn from somewhere
    box_sn = box_sn if box_sn else '9999999'

    if not box_sn:
        print('sqs_build_msg missing box_sn')
        os._exit(1)

    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    u = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    rv_up = sp.run('uptime', shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    plat = 'dev'
    if linux_is_rpi3():
        plat = 'rpi3'
    elif linux_is_rpi4():
        plat = 'rpi4'
    d = {
        'reason': rz,
        # todo > do this project thing, cannot be always osu
        'project': 'osu',
        'vessel': vn,
        'ddh_commit': dch,
        'utc_time': str(u),
        'local_time': str(t),
        'box_sn': box_sn,
        'hw_uptime': rv_up.stdout.decode(),
        'gps_position': '{},{}'.format(lat, lon),
        'platform': plat,
        'msg_ver': m_ver
    }
    return d
