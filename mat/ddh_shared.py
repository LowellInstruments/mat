import json
import os
import socket
from pathlib import Path
from mat.utils import linux_is_rpi


DDH_GUI_UDP_PORT = 12349
_sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_ddh_udp_gui(s, ip='127.0.0.1', port=DDH_GUI_UDP_PORT):
    assert '/' in s
    _sk.sendto(s.encode(), (ip, port))


def get_ddh_folder_path_root() -> Path:
    if linux_is_rpi():
        return Path.home() / 'li' / 'ddh'
    return Path.home() / 'PycharmProjects' / 'ddh'


r = get_ddh_folder_path_root()


def get_ddh_folder_path_dl_files() -> Path:
    return r / 'dl_files'


def get_ddh_folder_path_settings() -> Path:
    return r / 'settings'


def get_ddh_folder_path_res() -> Path:
    return r / 'ddh/gui/res'


def get_ddh_settings_file() -> Path:
    return r / 'settings/ddh.json'


def get_ddh_disabled_ble_file_flag() -> str:
    return '/tmp/ddh_disabled_ble_file_flag'


def get_ddh_db_history() -> str:
    return str(r / 'ddh/db/db_his.db')


def get_ddh_db_plots() -> str:
    return str(r / 'ddh/db/db_plt.db')


def get_ddh_db_macs() -> str:
    return str(r / 'ddh/db/db_macs.db')


def get_ddh_db_sns() -> str:
    return str(r / 'ddh/db/db_sns.db')


def get_ddh_file_mc_fallback() -> Path:
    return get_ddh_folder_path_dl_files() / 'MAT_fallback.cfg'


def get_ddh_file_version() -> str:
    return str(r / 'ddh/version.py')


def ddh_check_conf_json_file():
    try:
        j = str(get_ddh_settings_file())
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
    j = str(get_ddh_settings_file())
    try:
        with open(j) as f:
            cfg = json.load(f)
            known = cfg['db_logger_macs'].keys()
            return [x.lower() for x in known]
    except TypeError:
        return 'error json_get_macs()'


def ddh_get_json_plot_type():
    j = str(get_ddh_settings_file())
    with open(j) as f:
        cfg = json.load(f)
        v = cfg['last_haul']
        assert v in (0, 1)
        return v


def ddh_get_json_app_type():
    return ddh_get_json_plot_type()


def ddh_get_json_vessel_name():
    j = str(get_ddh_settings_file())
    try:
        with open(j) as f:
            cfg = json.load(f)
            return cfg['ship_name']
    except TypeError:
        return 'Unnamed ship'


def ddh_get_json_moving_speed() -> list:
    j = str(get_ddh_settings_file())
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

    j = str(get_ddh_settings_file())
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


def main():
    print(get_ddh_folder_path_root())


if __name__ == '__main__':
    main()
