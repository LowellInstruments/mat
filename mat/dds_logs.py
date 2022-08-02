import datetime
from pathlib import Path
import os


def _is_rpi():
    return os.uname().nodename in ('raspberrypi', 'rpi')


def _folder_logs():
    if _is_rpi():
        return Path.home() / 'li' / 'dds' / 'logs'
    return Path.home() / 'PycharmProjects' / 'dds' / 'logs'


class DDSLogs:
    @staticmethod
    def _gen_log_file_name(lbl) -> str:
        d = str(_folder_logs())
        Path(d).mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return '{}/{}_{}.log'.format(d, lbl, now)

    def __init__(self, label):
        self.label = label
        self.f_name = self._gen_log_file_name(label)

    def a(self, s):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        s = '{} [ {} ] {}'.format(now, self.label.upper(), s)
        with open(self.f_name, 'a') as f:
            f.write(s + '\n')


if __name__ == '__main__':
    lg = DDSLogs('my_log_Test')
    lg.a('iuhu')
