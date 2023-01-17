import asyncio
import json
import platform
from datetime import datetime, timezone, timedelta
import math
import time
import humanize
from bleak import BleakError, BleakClient
from mat.ble.ble_mat_utils import ble_mat_lowell_build_cmd as build_cmd, ble_mat_progress_dl, ble_mat_bluetoothctl_disconnect, \
    ble_mat_hci_exists
from mat.ble.bleak.cc26x2r_ans import is_cmd_done
from mat.logger_controller import SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, RWS_CMD, STATUS_CMD, LOGGER_INFO_CMD_W, \
    LOGGER_INFO_CMD
from mat.logger_controller_ble import DWG_FILE_CMD, CRC_CMD, CONFIG_CMD, WAKE_CMD, OXYGEN_SENSOR_CMD, BAT_CMD, \
    FILE_EXISTS_CMD, WAT_CMD
from mat.utils import lowell_cmd_dir_ans_to_dict


GPS_FRM_STR = '{:+.6f}'


class BleCC26X2Sim:
    def __init__(self, h='hci0', dbg_ans=False):
        self.is_connected = False
        self.mac = ''
        self.files = {'MAT.cfg': 189}
        self.gps_string = ''

    async def connect(self, mac):
        self.mac = None
        if mac.startswith('11:22:33'):
            self.mac = mac
            return 0
        return 1

    async def disconnect(self):
        self.mac = ''

    @staticmethod
    async def cmd_stm():
        return 0

    async def cmd_dwg(self, s):
        return 0 if s in self.files.keys() else 1

    async def cmd_crc(self, s):
        if s not in self.files.keys():
            return 1, ''
        return 0, '12345678'

    async def cmd_del(self, s):
        try:
            del self.files[s]
            return 0
        except (Exception, ):
            return 1

    async def cmd_fex(self, s):
        # todo > check if this exists on firmware
        return 0 if s in self.files.keys() else 1

    @staticmethod
    async def cmd_gtm():
        dt = datetime.now(timezone.utc)
        s_dt = dt.strftime('%Y/%m/%d %H:%M:%S')
        return 0, s_dt

    @staticmethod
    async def cmd_stp():
        return 0

    @staticmethod
    async def cmd_led():
        return 0

    async def cmd_frm(self):
        self.files = {}
        return 0

    async def cmd_sws(self, g):
        self.gps_string = g
        return 0

    async def cmd_rws(self, g):
        self.gps_string = g
        return 0

    async def cmd_mts(self):
        self.files['mts_file'] = 1245
        return 0

    async def cmd_dir(self) -> tuple:
        a = ''
        for k, v in self.files.items():
            a += '\n\r{}\t\t\t{}\n\r'.format(k, v)
        a += '\4\n\r'
        ls = lowell_cmd_dir_ans_to_dict(a.encode(), '*', match=True)
        return 0, ls

    async def cmd_cfg(self, cfg_d):
        assert type(cfg_d) is dict
        self.files['MAT.cfg'] = 189
        return 0

    @staticmethod
    async def cmd_wli(s):
        return 0

    @staticmethod
    async def cmd_gdo():
        return '1111', '2222', '3333'

    @staticmethod
    async def cmd_bat():
        return 0, 2456

    @staticmethod
    async def cmd_wat():
        return 0, 3000

    @staticmethod
    async def cmd_wak(s):
        assert s in ('on', 'off')
        return 0

    @staticmethod
    async def cmd_rli():
        # info = {'SN': '1234567',
        #         'BA': '1111',
        #         'CA': '2222',
        #         'MA': '3333333'}
        return 0

    @staticmethod
    async def cmd_sts():
        # running, stopped, delayed
        return 'stopped'

    @staticmethod
    async def cmd_run():
        return 0

    @staticmethod
    async def cmd_gfv():
        return 0, '4.4.44'

    @staticmethod
    async def cmd_dwl(z, ip=None, port=None) -> tuple:
        return 0, b'my_binary_data'

    async def cmd_utm(self):
        return 0, '3 days'
