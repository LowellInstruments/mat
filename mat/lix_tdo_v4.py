from mat.ascii85 import ascii85_to_num as a2n
from mat.lix import CS, LEN_LIX_FILE_CONTEXT, lix_mah_time_to_str, _p, lix_macro_header_start_time_to_seconds
from mat.lix_tdo_v3 import ParserLixTdoFileV3


LEN_LIX_FILE_CC_AREA = 5 * 33
LEN_LIX_FILE_CF_AREA = 5 * 9


# flag debug
debug = 0


class ParserLixTdoFileV4(ParserLixTdoFileV3):

    def _parse_macro_header(self):
        self.mah.bytes = self.bb[:CS]
        bb = self.mah.bytes
        self.mah.file_type = bb[:3]
        self.mah.file_version = bb[3]
        self.mah.timestamp = bb[4:10]
        self.mah.battery = bb[10:12]
        self.mah.hdr_idx = bb[12]
        # HSA macro-header must match firmware hsa.h
        i_mah = 13
        self.mah.cc_area = bb[i_mah: i_mah + LEN_LIX_FILE_CC_AREA]
        # context
        i = CS - LEN_LIX_FILE_CONTEXT
        self.mah.context = bb[i:]
        gfv = bb[i:i+4]
        i += 4
        rvn = bb[i]
        i += 1
        pfm = bb[i]
        i += 1
        self.mah_context.spn = bb[i]
        i += 1
        # we used to have PMA here but not anymore
        spt = bb[i:i + 5].decode()
        i += 5
        dro = bb[i:i + 5].decode()
        i += 5
        dru = bb[i:i + 5].decode()
        i += 5
        drf = bb[i:i + 2].decode()
        i += 2
        dso = bb[i:i + 5].decode()
        i += 5
        dsu = bb[i:i + 5].decode()

        # display all this info
        _p(f"\n\tMACRO header \t|  logger type {self.mah.file_type.decode()}")
        _p(f"\tfile version \t|  {self.mah.file_version}")
        self.mah.timestamp_str = lix_mah_time_to_str(self.mah.timestamp)

        _p(f"\tdatetime is   \t|  {self.mah.timestamp_str}")
        bat = int.from_bytes(self.mah.battery, "big")
        _p("\tbattery level \t|  0x{:04x} = {} mV".format(bat, bat))
        _p(f"\theader index \t|  {self.mah.hdr_idx}")
        if b"00004" != self.mah.cc_area[:5]:
            return {}
        _p("\tcc_area \t\t|  detected")
        pad = '\t\t\t\t\t   '
        _p(f'{pad}tmr = {a2n(self.mah.cc_area[10:15].decode())}')
        _p(f'{pad}tma = {a2n(self.mah.cc_area[15:20].decode())}')
        _p(f'{pad}tmb = {a2n(self.mah.cc_area[20:25].decode())}')
        _p(f'{pad}tmc = {a2n(self.mah.cc_area[25:30].decode())}')
        _p(f'{pad}tmd = {a2n(self.mah.cc_area[30:35].decode())}')
        _p(f'{pad}pra = {a2n(self.mah.cc_area[125:130].decode())}')
        _p(f'{pad}prb = {a2n(self.mah.cc_area[130:135].decode())}')
        # PRC / PRD are not ascii85, also, we need them
        self.prc = float(self.mah.cc_area[135:140].decode()) / 100
        self.prd = float(self.mah.cc_area[140:145].decode()) / 100
        _p(f'{pad}prc = {self.prc}')
        _p(f'{pad}prd = {self.prd}')
        _p(f'{pad}dco = {a2n(self.mah.cc_area[145:150].decode())}')
        _p(f'{pad}nco = {a2n(self.mah.cc_area[150:155].decode())}')
        _p(f'{pad}dhu = {a2n(self.mah.cc_area[155:160].decode())}')
        _p(f'{pad}dcd = {a2n(self.mah.cc_area[160:165].decode())}')
        _p("\tcontext \t\t|  detected")
        _p(f'{pad}gfv = {gfv}')
        _p(f'{pad}rvn = {rvn}')
        _p(f'{pad}pfm = {pfm}')
        _p(f'{pad}spn = {self.mah_context.spn}')
        _p(f'{pad}spt = {spt}')
        _p(f'{pad}dro = {dro}')
        _p(f'{pad}dru = {dru}')
        _p(f'{pad}drf = {drf}')
