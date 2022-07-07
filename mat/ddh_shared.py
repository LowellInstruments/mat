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


def get_ddh_folder_path_dl_logs() -> Path:
    return r / 'logs'


def get_ddh_folder_path_res() -> Path:
    return r / 'ddh/gui/res'


def get_ddh_folder_path_settings() -> Path:
    return r / 'ddh/gui/settings'


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


def main():
    print(get_ddh_folder_path_root())


if __name__ == '__main__':
    main()
