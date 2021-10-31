import time
import bluepy


def ble_connect_rn4020_logger(lc):
    # prevents running all being non-root
    # assert ble_linux_write_parameters_as_fast(lc.h)

    uuid_s = '00035b03-58e6-07dd-021a-08123a000300'
    uuid_c = '00035b03-58e6-07dd-021a-08123a000301'

    try:
        lc.per = bluepy.btle.Peripheral(lc.mac, iface=lc.h, timeout=10)
        lc.per.setDelegate(lc.dlg)
        lc.svc = lc.per.getServiceByUUID(uuid_s)
        lc.cha = lc.svc.getCharacteristics(uuid_c)[0]
        desc = lc.cha.valHandle + 1
        lc.per.writeCharacteristic(desc, b'\x01\x00')
        # do not remove, damn Jim
        time.sleep(.5)
        return True

    except (AttributeError, bluepy.btle.BTLEException) as ex:
        print('[ BLE ] cannot connect')
        return False


# def ble_file_list_as_dict(ls, ext, match=True):
#     if ls is None:
#         return {}
#
#     err = ERR_MAT_ANS.encode()
#     if err in ls:
#         return err
#
#     if type(ext) is str:
#         ext = ext.encode()
#
#     files, idx = {}, 0
#
#     # ls: b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r\n\rMAT.cfg\t\t\t189\n\r\x04\n\r'
#     ls = ls.split()
#     while idx < len(ls):
#         name = ls[idx]
#         if name in [b'\x04']:
#             break
#
#         # wild-card case
#         if ext == b'*' and name not in [b'.', b'..']:
#             files[name.decode()] = int(ls[idx + 1])
#         # specific extension case
#         elif name.endswith(ext) == match and name not in [b'.', b'..']:
#             files[name.decode()] = int(ls[idx + 1])
#         idx += 2
#     return files
#
#
# def ble_cmd_file_list_only_lid_files(lc) -> dict:
#     return lc.ble_cmd_dir_ext(b'lid')
#
#
# def utils_logger_is_rn4020(mac):
#     return mac.startswith('00:1e:c0')
