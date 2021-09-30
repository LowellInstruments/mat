import crc16


def xmd_frame_check_crc(lc):
    data = lc.dlg.x_buf[3:-2]
    rx_crc = lc.dlg.x_buf[-2:]
    calc_crc_int = crc16.crc16xmodem(data)
    calc_crc_bytes = calc_crc_int.to_bytes(2, byteorder='big')
    return calc_crc_bytes == rx_crc
