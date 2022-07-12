import json
import os
import socket
from pathlib import Path
import pandas as pd
from mat.data_converter import default_parameters, DataConverter
from mat.data_file_factory import load_data_file
from mat.utils import linux_is_rpi, linux_ls_by_ext


DDH_GUI_UDP_PORT = 12349
_sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_ddh_udp_gui(s, ip='127.0.0.1', port=DDH_GUI_UDP_PORT):
    if '/' not in s:
        s += '/'
    _sk.sendto(s.encode(), (ip, port))


def get_ddh_folder_path_root() -> Path:
    if linux_is_rpi():
        return Path.home() / 'li' / 'ddh'
    return Path.home() / 'PycharmProjects' / 'ddh'


def get_dds_folder_path_root():
    if linux_is_rpi():
        return Path.home() / 'li' / 'dds'
    return Path.home() / 'PycharmProjects' / 'dds'


rh = get_ddh_folder_path_root()
rs = get_dds_folder_path_root()


def get_ddh_folder_path_res() -> Path:
    return rh / 'ddh/gui/res'


def get_dds_settings_file() -> Path:
    return rs / 'settings/ddh.json'


def get_ddh_disabled_ble_file_flag() -> str:
    return '/tmp/ddh_disabled_ble_file.flag'


def get_ddh_app_override_file_flag() -> str:
    return '/tmp/ddh_app_override_file.flag'


def get_ddh_sns_force_file_flag() -> str:
    return '/tmp/ddh_sns_force_file.flag'


def get_ddh_black_macs_purge_file_flag() -> str:
    return '/tmp/ddh_black_macs_purge_file.flag'


def get_dds_aws_has_something_to_do_flag() -> str:
    return '/tmp/ddh_aws_has_something_to_do.flag'


def get_dds_is_ble_downloading_flag() -> str:
    return '/tmp/get_dds_is_ble_downloading_flag'


def get_ddh_db_history() -> str:
    return str(rh / 'ddh/db/db_his.db')


def get_ddh_db_sns() -> str:
    return str(rs / 'dds/db/db_sns.db')


def get_ddh_db_plots() -> str:
    return str(rh / 'ddh/db/db_plt.db')


def get_ddh_file_mc_fallback() -> Path:
    return get_dds_folder_path_dl_files() / 'MAT_fallback.cfg'


def get_ddh_file_version() -> str:
    return str(rh / 'ddh/version.py')


def ddh_check_conf_json_file():
    try:
        j = str(get_dds_settings_file())
        with open(j) as f:
            cfg = json.load(f)
            del cfg['db_logger_macs']
            del cfg['ship_name']
            del cfg['forget_time']
            del cfg['metrics']
            del cfg['span_dict']
            del cfg['units_temp']
            del cfg['units_depth']
            del cfg['last_haul']
            del cfg['moving_speed']
            del cfg['comment-1']
            assert cfg == {}

    except KeyError as ke:
        print('ddh.json misses key {}'.format(ke))
        return 1

    except AssertionError:
        print('ddh.json has unknown key')
        return 1

    except (Exception, ) as ex:
        print(ex)
        return 1


def ddh_get_macs_from_json_file():
    j = str(get_dds_settings_file())
    try:
        with open(j) as f:
            cfg = json.load(f)
            known = cfg['db_logger_macs'].keys()
            return [x.lower() for x in known]
    except TypeError:
        return 'error json_get_macs()'


def ddh_get_json_plot_type():
    j = str(get_dds_settings_file())
    with open(j) as f:
        cfg = json.load(f)
        v = cfg['last_haul']
        assert v in (0, 1)
        return v


def ddh_get_json_app_type():
    return ddh_get_json_plot_type()


def dds_get_json_vessel_name():
    j = str(get_dds_settings_file())
    try:
        with open(j) as f:
            cfg = json.load(f)
            return cfg['ship_name']
    except TypeError:
        return 'Unnamed ship'


def dds_get_json_moving_speed() -> list:
    j = str(get_dds_settings_file())
    try:
        with open(j) as f:
            cfg = json.load(f)
            max_n_min = list(cfg['moving_speed'].values())
            assert len(max_n_min) == 2
            assert max_n_min[0] <= max_n_min[1]
            return max_n_min
    except TypeError:
        print('error json_get_moving_speed()')


def _mac_dns_no_case(mac):
    """ returns logger name from its mac, not case-sensitive """

    j = str(get_dds_settings_file())
    try:
        with open(j) as f:
            cfg = json.load(f)
            return cfg['db_logger_macs'][mac]
    except (FileNotFoundError, TypeError, KeyError):
        return None


def ddh_get_json_mac_dns(mac):
    """ returns non-case-sensitive logger name (known) or mac (unknown) """

    # check for both upper() and lower() cases
    name = _mac_dns_no_case(mac.lower())
    if not name:
        name = _mac_dns_no_case(mac.upper())
    rv = name if name else mac
    return rv


def get_mac_from_folder_path(fol):
    """ returns '11:22:33' from 'dl_files/11-22-33' """

    try:
        return fol.split('/')[-1].replace('-', ':')
    except (ValueError, Exception):
        return None


def get_dl_folder_path_from_mac(mac):
    """ returns 'dl_files/11-22-33' from '11:22:33' """

    fol = get_dds_folder_path_dl_files()
    fol = fol / '{}/'.format(mac.replace(':', '-').lower())
    return fol


def create_folder_logger_by_mac(mac):
    """ mkdir folder based on mac, replaces ':' with '-' """

    fol = get_dds_folder_path_dl_files()
    fol = fol / '{}/'.format(mac.replace(':', '-').lower())
    os.makedirs(fol, exist_ok=True)
    return fol


def ddh_get_commit():
    import git
    _r = git.Repo(get_ddh_folder_path_root())
    c = _r.head.commit
    return str(c)[:5]


def dds_get_commit():
    import git
    _r = git.Repo(get_dds_folder_path_root())
    c = _r.head.commit
    return str(c)[:5]


BAROMETRIC_PRESSURE_SEA_LEVEL_IN_DECIBAR = 10.1
DDH_BPSL = BAROMETRIC_PRESSURE_SEA_LEVEL_IN_DECIBAR
_g_files_we_cannot_convert = []


def _lid_file_has_sensor_data_type(path, suffix):
    _map = {
        '_DissolvedOxygen': 'DOS',
        '_Temperature': 'TMP',
        '_Pressure': 'PRS'
    }
    header = load_data_file(path).header()
    return header.tag(_map[suffix])


def ddh_convert_lid_to_csv(fol, suf) -> (bool, list):

    if not Path(fol).is_dir():
        print('[ CNV ] error -> folder {} not found'.format(fol))
        return False, []

    # ---------------------------
    # check asked suffix exists
    # ---------------------------
    valid_suffixes = ('_DissolvedOxygen', '_Temperature', '_Pressure')
    if suf not in valid_suffixes:
        print('[ CNV ] error -> unknown suffix {}'.format(suf))
        return False, []

    # needed variables for conversion
    parameters = default_parameters()
    err_files = []
    all_ok = True
    global _g_files_we_cannot_convert
    lid_files = linux_ls_by_ext(fol, 'lid')

    # ----------------------------------------------
    # iterate all lid files in this logger's folder
    # ----------------------------------------------
    for f in lid_files:

        # skip already converted files
        _ = '{}{}.csv'.format(f.split('.')[0], suf)
        if Path(_).is_file():
            continue

        # skip files we know as bad ones
        if f in _g_files_we_cannot_convert:
            continue

        # ---------------
        # try to convert
        # ---------------
        try:

            # skip files not containing this sensor data
            if not _lid_file_has_sensor_data_type(f, suf):
                # s = '[ CNV ] file {} -> no {} data'
                # l_d_(s.format(f, suf))
                continue

            DataConverter(f, parameters).convert()
            print('[ CNV ] {}, suffix {}'.format(f, suf))

            # --------------------------------
            # hack for RN4020 pressure adjust
            # --------------------------------
            if ('_Pressure' in suf) and ('moana' not in f):
                print('[ CNV ] adjusting LI file {}'.format(f))
                # f: ends with.lid
                fp_csv = f[:-4] + '_Pressure.csv'
                df = pd.read_csv(fp_csv)
                c = 'Pressure (dbar)'
                df[c] = df['Pressure (dbar)'] - DDH_BPSL
                df[c] = df[c].apply(lambda x: x if x > 0 else 0)
                df.to_csv(fp_csv, index=False)

        except (ValueError, Exception) as ve:
            all_ok = False
            err_files.append(f)
            print('[ CNV ] error {} -> {}'.format(f, ve))
            if f not in _g_files_we_cannot_convert:
                print('[ CNV ] error: ignoring file {} from now on'.format(f))
                _g_files_we_cannot_convert.append(f)

    return all_ok, err_files


def get_dds_folder_path_dl_files() -> Path:
    return rs / 'dl_files'


def get_dds_folder_path_logs() -> Path:
    return rs / 'logs'


def get_dds_folder_path_macs() -> Path:
    return rs / 'macs'


def get_dds_folder_path_macs_black() -> Path:
    return get_dds_folder_path_macs() / 'black'


def get_dds_folder_path_sns() -> Path:
    return rs / 'sns'


def get_dds_folder_path_settings() -> Path:
    return rs / 'settings'


def get_dds_loggers_forget_time() -> int:
    j = str(get_dds_settings_file())
    try:
        with open(j) as f:
            cfg = json.load(f)
            return cfg['forget_time']

    except (FileNotFoundError, TypeError, KeyError):
        return -1


def main():
    print(get_ddh_folder_path_root())


if __name__ == '__main__':
    main()
