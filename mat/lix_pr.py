import traceback

from mat.lix_dox import ParserLixDoxFile
from mat.lix_tdo_v3 import ParserLixTdoFileV3
from mat.lix_tdo_v4 import ParserLixTdoFileV4


def get_tdo_parser(rvn):
    # rvn: 52
    rvn = chr(rvn)
    if rvn == '3':
        return ParserLixTdoFileV3
    elif rvn == '4':
        return ParserLixTdoFileV4


def convert_lix_file(fp, more_columns=0):
    # fp: absolute file_path
    try:
        with open(fp, 'rb') as f:
            # ft: file type
            bb = f.read()
            ft = bb[:3]

            # pr: parser
            if ft in (b'DO1', b'DO2'):
                pr = ParserLixDoxFile
                pr = pr(fp)
            else:
                rvn_scc = bb[17]
                pr = get_tdo_parser(rvn_scc)
                pr = pr(fp, more_columns)
            pr.convert()
            return 0

    except (Exception, ) as ex:
        traceback.print_exc()
        print(f'error: parse_lix_file ex -> {ex}')
        return 1


if __name__ == '__main__':
    filename = '/home/kaz/Downloads/1111111_TST_20240819_173536.lid'
    convert_lix_file(filename, more_columns=1)
