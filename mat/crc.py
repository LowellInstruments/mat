import zlib


def calculate_local_file_crc(name):
    try:
        prev = 0
        for eachLine in open(name, "rb"):
            prev = zlib.crc32(eachLine, prev)
        return "%X" % (prev & 0xFFFFFFFF)
    except Exception as ex:
        print(ex)
        return False


if __name__ == '__main__':
    # 1E8C58BC file contents '1234567890 abcdef!!"
    # aeef2a50 file contents 'abcdefgh'
    print(calculate_local_file_crc("file.txt"))
