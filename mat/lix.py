import traceback

from mat.lix_dox import ParserLixDoxFile
from mat.lix_tdo import ParserLixTdoFile


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
    p = '/home/kaz/Downloads/dl_bil/60-77-71-22-CA-6D/2222222_tst_20240202_150848.lix'
    convert_lix_file(p)
