from datetime import datetime, timezone
from mat.utils import lowell_cmd_dir_ans_to_dict


GPS_FRM_STR = '{:+.6f}'


class BleCC26X2Sim:
    def __init__(self, h='hci0', dbg_ans=False):
        self.is_connected = False
        self.status = 'stopped'
        self.mac = ''
        self.files = {'MAT.cfg': 189}
        self.gps_string = ''
        self.info = {
            'SN': 'XXXXXXX',
            'MA': 'YYYY',
            'CA': 'ZZZZ',
            'BA': 'BBBBBBB'
        }

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

    async def cmd_stp(self):
        self.status = 'stopped'
        return 0

    @staticmethod
    async def cmd_led():
        return 0

    async def cmd_frm(self):
        self.files = {}
        return 0

    async def cmd_sws(self, g):
        self.status = 'stopped'
        self.gps_string = g
        return 0

    async def cmd_rws(self, g):
        if self.status in ('running', 'delayed'):
            return 1
        self.status = 'running'
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
        if self.status in ('running', 'delayed'):
            return 1
        self.files['MAT.cfg'] = 189
        return 0

    async def cmd_wli(self, s):
        i = s[:2]
        v = s[2:]
        self.info[i] = v
        if i not in ('SN', 'CA', 'BA', 'MA'):
            return 1

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

    async def cmd_sts(self):
        # running, stopped, delayed
        return 0, self.status

    async def cmd_run(self):
        if self.status in ('running', 'delayed'):
            return 1
        self.status = 'running'
        return 0

    @staticmethod
    async def cmd_gfv():
        return 0, '4.4.44'

    @staticmethod
    async def cmd_dwl(z, ip=None, port=None) -> tuple:
        return 0, b'my_binary_data'

    @staticmethod
    async def cmd_utm():
        return 0, '3 days'
