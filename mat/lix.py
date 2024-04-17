import traceback

from mat.lix_dox import ParserLixDoxFile
from mat.lix_tdo import ParserLixTdoFile


LID_FILE_UNK = 0
LID_FILE_V1 = 1
LID_FILE_V2 = 2


def id_lid_file_flavor(fp):
    """
    we don't use the word version here, just if it is an old
    LID file or a new LID file (LIX)
    :param fp: absolute file_path
    :return:
    """
    if not fp.endswith('.lid'):
        return 0

    try:
        with open(fp, 'rb') as f:
            # ft: file type
            bb = f.read()
            ft = bb[:3]

            # pr: parser
            if ft in (b'DO1', b'DO2', b'TDO'):
                return LID_FILE_V2
            elif ft in (b'PRF', b'TAP'):
                print('**************************************')
                print('ft LOGGER HEADER IS OLD, REFLASH IT ->', ft)
                print('**************************************')
                return LID_FILE_V2
            else:
                return LID_FILE_V1

    except (Exception,) as ex:
        traceback.print_exc()
        print(f'error: id_lid_file_flavor ex -> {ex}')
        return LID_FILE_UNK


def lid_file_v2_has_sensor_data_type(fp, suf):
    if not fp.endswith('.lid'):
        return 0

    try:
        with open(fp, 'rb') as f:
            # ft: file type
            bb = f.read()
            ft = bb[:3]

            if suf == "_DissolvedOxygen" and ft in (b'DO1', b'DO2'):
                return 1
            if suf == "_TDO" and ft in (b'TDO', ):
                return 1

    except (Exception,) as ex:
        traceback.print_exc()
        print(f'error: lid_file_v2_has_sensor_data_type ex -> {ex}')
        return LID_FILE_UNK


def convert_lix_file(fp):
    # fp: absolute file_path
    try:
        with open(fp, 'rb') as f:
            # ft: file type
            bb = f.read()
            ft = bb[:3]

            # pr: parser
            if ft in (b'DO1', b'DO2'):
                pr = ParserLixDoxFile(fp)
            else:
                pr = ParserLixTdoFile(fp)
            pr.convert()
            return 0

    except (Exception, ) as ex:
        traceback.print_exc()
        print(f'error: parse_lix_file ex -> {ex}')
        return 1


if __name__ == '__main__':
    # p = '/home/kaz/Downloads/dl_bil/9999999_BIL_20240122_195627.lix'
    p = '/home/kaz/Downloads/dl_bil/D0-2E-AB-D9-29-48/1111111_BIL_20240417_174624.lid'
    convert_lix_file(p)
