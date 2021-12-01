import pathlib
from mat.ble.bleak_beta.examples.do2.convert import cnv


if __name__ == '__main__':
    name = 'dummy_425.lid'
    s = pathlib.Path.home() / 'Downloads' / name
    cnv(s)
