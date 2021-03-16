import zlib


def calculate_local_file_crc(name) -> str:
    try:
        prev = 0
        for eachLine in open(name, "rb"):
            prev = zlib.crc32(eachLine, prev)
        # 1A2C34 formatted as '0012a2c34'
        return '%08x' % (prev & 0xFFFFFFFF)
    except Exception as ex:
        print(ex)
        return ''


if __name__ == '__main__':
    # 1E8C58BC file contents '1234567890 abcdef!!"
    # aeef2a50 file contents 'abcdefgh'
    print(calculate_local_file_crc("file.txt"))
